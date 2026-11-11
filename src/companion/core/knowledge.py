import logging
import re
from collections.abc import Callable
from dataclasses import replace
from pathlib import PurePath
from uuid import UUID

from companion.core.models import (
    EmbeddedChunk,
    KnowledgeDocument,
    KnowledgeFileType,
    KnowledgeStatus,
    KnowledgeUpload,
)
from companion.core.ports import (
    Clock,
    DocumentTextExtractor,
    Embedder,
    KnowledgeVectorStore,
    Repositories,
    TextExtractionError,
)

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
CHUNK_MAX_CHARACTERS = 1_000
FILE_TYPES_BY_EXTENSION = {
    ".txt": KnowledgeFileType.TEXT,
    ".md": KnowledgeFileType.MARKDOWN,
    ".markdown": KnowledgeFileType.MARKDOWN,
    ".pdf": KnowledgeFileType.PDF,
}
NO_TEXT_REASONS = {
    KnowledgeFileType.TEXT: "The file has no text.",
    KnowledgeFileType.MARKDOWN: "The file has no text.",
    KnowledgeFileType.PDF: "Scanned PDF — no text found",
}
INDEXING_FAILED_REASON = "Couldn’t index the document. Try again."
BLANK_LINE = re.compile(r"\n\s*\n")
SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


class KnowledgeDocumentNotFoundError(LookupError):
    """Raised when no Knowledge document has the given ID."""


class InvalidKnowledgeDocumentError(ValueError):
    """Raised when an uploaded Knowledge document is not valid."""


class KnowledgeNotRetryableError(ValueError):
    """Raised when asked to retry a Knowledge document that has not failed."""


def knowledge_file_type(file_name: str) -> KnowledgeFileType:
    """Tell what kind of Knowledge file a file is from its name.

    Args:
        file_name: The file's name, e.g. "dhammapada.pdf".

    Returns:
        The kind of file.

    Raises:
        InvalidKnowledgeDocumentError: If it is not text, Markdown or PDF.
    """
    extension = PurePath(file_name).suffix.lower()
    if extension not in FILE_TYPES_BY_EXTENSION:
        raise InvalidKnowledgeDocumentError(
            "Upload a text (.txt), Markdown (.md) or PDF (.pdf) file."
        )
    return FILE_TYPES_BY_EXTENSION[extension]


def pack(parts: list[str], separator: str, max_characters: int) -> list[str]:
    """Join parts in order into as few pieces as fit within a length.

    Args:
        parts: The parts, each no longer than `max_characters`.
        separator: What goes between two parts in one piece.
        max_characters: The longest a piece may be.

    Returns:
        The pieces.
    """
    pieces: list[str] = []
    current = ""
    for part in parts:
        joined = f"{current}{separator}{part}" if current else part
        if len(joined) <= max_characters:
            current = joined
        else:
            pieces.append(current)
            current = part
    if current:
        pieces.append(current)
    return pieces


def split_long_paragraph(paragraph: str, max_characters: int) -> list[str]:
    """Split a paragraph that is too long by sentence, then by word.

    Args:
        paragraph: The paragraph, on one line.
        max_characters: The longest a piece may be.

    Returns:
        Pieces no longer than `max_characters`, in order.
    """
    if len(paragraph) <= max_characters:
        return [paragraph]
    parts: list[str] = []
    for sentence in SENTENCE_END.split(paragraph):
        if len(sentence) <= max_characters:
            parts.append(sentence)
            continue
        words = [
            word[start : start + max_characters]
            for word in sentence.split()
            for start in range(0, len(word), max_characters)
        ]
        parts.extend(pack(words, " ", max_characters))
    return pack(parts, " ", max_characters)


def split_into_chunks(
    text: str, max_characters: int = CHUNK_MAX_CHARACTERS
) -> list[str]:
    """Split a document's text into chunks small enough to embed well.

    Paragraphs are kept whole where they fit, and neighbouring paragraphs
    share a chunk while there is room. Line breaks inside a paragraph, as PDFs
    have, become spaces.

    Args:
        text: The document's text.
        max_characters: The longest a chunk may be.

    Returns:
        The chunks in reading order; none if the text is blank.
    """
    pieces: list[str] = []
    for block in BLANK_LINE.split(text):
        paragraph = " ".join(block.split())
        if paragraph:
            pieces.extend(split_long_paragraph(paragraph, max_characters))
    return pack(pieces, "\n\n", max_characters)


class KnowledgeService:
    """Lets Admins build the Knowledge library the Companion draws on.

    An uploaded document starts pending. Ingestion reads its text, splits it
    into chunks, embeds them and stores them; then the document is ready for
    replies, or failed with a reason Admins can read.
    """

    def __init__(
        self,
        repositories: Repositories,
        text_extractor: DocumentTextExtractor,
        embedder: Embedder,
        vector_store: KnowledgeVectorStore,
        clock: Clock,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Knowledge documents are stored.
            text_extractor: Reads the text out of uploaded files.
            embedder: Turns chunks into embeddings.
            vector_store: Stores the chunks' embeddings.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._text_extractor = text_extractor
        self._embedder = embedder
        self._vector_store = vector_store
        self._clock = clock

    def list_documents(self) -> list[KnowledgeDocument]:
        """List every Knowledge document, newest upload first.

        Returns:
            The documents.
        """
        return self._repositories.knowledge_documents.list_all()

    def upload(self, upload: KnowledgeUpload) -> KnowledgeDocument:
        """Save a new Knowledge document as pending, ready to be ingested.

        Args:
            upload: The document and its file.

        Returns:
            The saved, pending document.

        Raises:
            InvalidKnowledgeDocumentError: If the title, source or tradition
                is blank, or the file is empty or too big.
        """
        title = upload.title.strip()
        source = upload.source.strip()
        tradition = upload.tradition.strip()
        if not title:
            raise InvalidKnowledgeDocumentError("A document needs a title.")
        if not source:
            raise InvalidKnowledgeDocumentError("A document needs a source or author.")
        if not tradition:
            raise InvalidKnowledgeDocumentError("A document needs a tradition.")
        if not upload.content:
            raise InvalidKnowledgeDocumentError("The file is empty.")
        if len(upload.content) > MAX_UPLOAD_BYTES:
            raise InvalidKnowledgeDocumentError("The file is bigger than 20 MB.")
        return self._repositories.knowledge_documents.add(
            replace(upload, title=title, source=source, tradition=tradition),
            self._clock.now(),
        )

    def ingest(self, document_id: UUID) -> None:
        """Read, chunk, embed and store a pending document's text.

        The document ends up ready, or failed with the reason. A document
        deleted meanwhile is left alone.

        Args:
            document_id: The document's ID.
        """
        documents = self._repositories.knowledge_documents
        document = documents.get(document_id)
        if document is None:
            return
        try:
            text = self._text_extractor.extract(
                document.file_type, documents.get_content(document_id)
            )
        except TextExtractionError as error:
            self._fail(document_id, str(error))
            return
        chunks = split_into_chunks(text)
        if not chunks:
            self._fail(document_id, NO_TEXT_REASONS[document.file_type])
            return
        try:
            embeddings = self._embedder.embed_passages(chunks)
            self._vector_store.replace_chunks(
                document_id,
                [
                    EmbeddedChunk(text=chunk, embedding=embedding)
                    for chunk, embedding in zip(chunks, embeddings, strict=True)
                ],
            )
        except Exception:
            logger.exception("Could not index Knowledge document %s", document_id)
            self._fail(document_id, INDEXING_FAILED_REASON)
            return
        documents.set_status(document_id, KnowledgeStatus.READY, failure_reason=None)

    def retry(self, document_id: UUID) -> KnowledgeDocument:
        """Make a failed document pending again, ready to be ingested again.

        Args:
            document_id: The document's ID.

        Returns:
            The pending document.

        Raises:
            KnowledgeDocumentNotFoundError: If there is no such document.
            KnowledgeNotRetryableError: If the document has not failed.
        """
        document = self._get(document_id)
        if document.status != KnowledgeStatus.FAILED:
            raise KnowledgeNotRetryableError(document_id)
        pending = self._repositories.knowledge_documents.set_status(
            document_id, KnowledgeStatus.PENDING, failure_reason=None
        )
        if pending is None:
            raise KnowledgeDocumentNotFoundError(document_id)
        return pending

    def delete(self, document_id: UUID) -> None:
        """Remove a document and its chunks, so replies no longer use it.

        Args:
            document_id: The document's ID.

        Raises:
            KnowledgeDocumentNotFoundError: If there is no such document.
        """
        self._get(document_id)
        self._vector_store.delete_chunks(document_id)
        self._repositories.knowledge_documents.delete(document_id)

    def seed_starter_set(
        self, read_starter_set: Callable[[], list[KnowledgeUpload]]
    ) -> None:
        """Upload and ingest the starter documents on first run.

        Nothing is loaded once any document exists, so a document an Admin
        deleted never comes back.

        Args:
            read_starter_set: Reads the starter documents from the seed files.
        """
        if self._repositories.knowledge_documents.list_all():
            return
        for upload in read_starter_set():
            self.ingest(self.upload(upload).id)

    def _get(self, document_id: UUID) -> KnowledgeDocument:
        """Find a Knowledge document.

        Args:
            document_id: The document's ID.

        Returns:
            The document.

        Raises:
            KnowledgeDocumentNotFoundError: If there is none.
        """
        document = self._repositories.knowledge_documents.get(document_id)
        if document is None:
            raise KnowledgeDocumentNotFoundError(document_id)
        return document

    def _fail(self, document_id: UUID, reason: str) -> None:
        """Mark a document failed with the reason Admins are shown.

        Args:
            document_id: The document's ID.
            reason: Why it failed.
        """
        self._repositories.knowledge_documents.set_status(
            document_id, KnowledgeStatus.FAILED, failure_reason=reason
        )
