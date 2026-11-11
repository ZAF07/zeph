from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from companion.core.models import KnowledgeFileType
from companion.core.ports import TextExtractionError


class PypdfTextExtractor:
    """Reads text from text and Markdown files, and from PDFs with pypdf."""

    def extract(self, file_type: KnowledgeFileType, content: bytes) -> str:
        """Read a file's text.

        Text and Markdown must be UTF-8. A PDF's pages are read in order; a
        scanned PDF has no text, so it gives blank text.

        Args:
            file_type: What kind of file it is.
            content: The file's bytes.

        Returns:
            The text, which may be blank if the file has none.

        Raises:
            TextExtractionError: If the file can't be read.
        """
        if file_type != KnowledgeFileType.PDF:
            try:
                return content.decode("utf-8-sig")
            except UnicodeDecodeError as error:
                raise TextExtractionError(
                    "Couldn’t read the text. Save the file as UTF-8 and try again."
                ) from error
        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise TextExtractionError("The PDF is password-protected.")
            return "\n\n".join(page.extract_text() or "" for page in reader.pages)
        except (PyPdfError, ValueError, OSError) as error:
            raise TextExtractionError("Couldn’t read this PDF.") from error
