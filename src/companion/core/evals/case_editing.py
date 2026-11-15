import re
from typing import Any
from uuid import uuid4

from companion.core.errors import ConflictError, InvalidError, NotFoundError
from companion.core.evals.case_shapes import (
    CASE_SHAPES,
    FormShape,
    find_problems,
    image_fields,
)
from companion.core.evals.cases import InvalidEvalCaseError
from companion.core.evals.eval_checks import read_case
from companion.core.evals.models import EvalCase, EvalImage, EvalName, StoredEvalCase
from companion.core.evals.ports import EvalCaseRepository, EvalImageRepository
from companion.core.models import User
from companion.core.ports import Clock

CASE_KEY = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
CASE_KEY_MAX_LENGTH = 60
IMAGE_MEDIA_TYPES = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
IMAGE_MAX_BYTES = 5 * 1024 * 1024


class EvalCaseNotFoundError(NotFoundError):
    """Raised when no Eval Case has the key asked for."""

    shown_message = "No such Eval Case."


class ArchivedEvalCaseError(ConflictError):
    """Raised when an archived case is changed; archived cases stay as they were."""

    shown_message = "This case is archived, so it can't be changed."


class EvalImageNotFoundError(NotFoundError):
    """Raised when no test image has the name asked for."""

    shown_message = "No such image."


class InvalidEvalImageError(InvalidError):
    """Raised when an uploaded test image is not a PNG, JPEG or WebP, or too big."""

    shown_message = "Upload a PNG, JPEG or WebP image of at most 5 MB."


def require_no_problems(problems: dict[str, str]) -> None:
    """Refuse a case save when any field has a problem.

    Args:
        problems: A message per field path.

    Raises:
        InvalidEvalCaseError: If there is any problem.
    """
    if problems:
        raise InvalidEvalCaseError("The case has problems; see each field.", problems)


def image_name_stem(file_name: str) -> str:
    """Turn an uploaded file's name into the start of a stored image's name.

    Args:
        file_name: The uploaded file's name, e.g. "My Drawing.PNG".

    Returns:
        Lowercase letters and numbers joined by hyphens, e.g. "my-drawing";
        "image" when nothing is left.
    """
    words = re.findall(r"[a-z0-9]+", file_name.rsplit(".", 1)[0].lower())
    return "-".join(words) or "image"


class EvalCaseService:
    """Lets Admins add, edit, duplicate and archive Eval Cases (ADR-0004).

    Each Eval's case shape checks every save, so a run never meets a case
    it can't read. Edits stay in the database; they never go back to the
    seed files.
    """

    def __init__(
        self, cases: EvalCaseRepository, images: EvalImageRepository, clock: Clock
    ) -> None:
        """Set up the service.

        Args:
            cases: Where Eval Cases are stored.
            images: Where the cases' test images are stored.
            clock: Tells the time.
        """
        self._cases = cases
        self._images = images
        self._clock = clock

    def shapes(self) -> dict[EvalName, FormShape]:
        """Give every Eval's case shape, which draws its form.

        Returns:
            The shape of each Eval's cases.
        """
        return CASE_SHAPES

    def list_cases(self, eval_name: EvalName) -> list[StoredEvalCase]:
        """List every case of one Eval, archived ones too.

        Args:
            eval_name: The Eval.

        Returns:
            The cases, in the order added.
        """
        return self._cases.list_stored(eval_name)

    def get_case(self, key: str) -> StoredEvalCase:
        """Read one case.

        Args:
            key: Its key.

        Returns:
            The case.

        Raises:
            EvalCaseNotFoundError: If no case has the key.
        """
        stored = self._cases.get(key)
        if stored is None:
            raise EvalCaseNotFoundError()
        return stored

    def add_case(
        self, admin: User, key: str, eval_name: EvalName, content: dict[str, Any]
    ) -> StoredEvalCase:
        """Add a case an Admin wrote.

        Args:
            admin: The Admin adding it.
            key: Its key, e.g. `reminded-of-sister`, unique across Evals.
            eval_name: Its Eval.
            content: The case, in its Eval's case shape.

        Returns:
            The case.

        Raises:
            InvalidEvalCaseError: If the key or content doesn't fit, with a
                message per field.
        """
        case = EvalCase(key=key, eval=eval_name, content=content)
        require_no_problems({**self._key_problems(key), **self._content_problems(case)})
        if not self._cases.add(case, self._clock.now(), admin.id):
            raise InvalidEvalCaseError(
                "The case key is taken.", {"key": "Another case has this key."}
            )
        return self.get_case(key)

    def edit_case(
        self, admin: User, key: str, content: dict[str, Any]
    ) -> StoredEvalCase:
        """Change a case's content; the next run uses it, old runs keep theirs.

        Args:
            admin: The Admin changing it.
            key: Its key.
            content: Its new content, in its Eval's case shape.

        Returns:
            The case.

        Raises:
            EvalCaseNotFoundError: If no case has the key.
            ArchivedEvalCaseError: If the case is archived.
            InvalidEvalCaseError: If the content doesn't fit, with a message
                per field.
        """
        stored = self.get_case(key)
        if stored.case.archived:
            raise ArchivedEvalCaseError()
        case = EvalCase(key=key, eval=stored.case.eval, content=content)
        require_no_problems(self._content_problems(case))
        self._cases.update(
            key, content, archived=False, now=self._clock.now(), admin_id=admin.id
        )
        return self.get_case(key)

    def duplicate_case(self, admin: User, key: str, new_key: str) -> StoredEvalCase:
        """Copy a case under a new key, to make a similar case quickly.

        Args:
            admin: The Admin copying it.
            key: The case to copy.
            new_key: The copy's key.

        Returns:
            The copy.

        Raises:
            EvalCaseNotFoundError: If no case has the key.
            InvalidEvalCaseError: If the new key doesn't fit or is taken.
        """
        stored = self.get_case(key)
        return self.add_case(admin, new_key, stored.case.eval, stored.case.content)

    def archive_case(self, admin: User, key: str) -> StoredEvalCase:
        """Archive a case: new runs leave it out, old runs still show it.

        Args:
            admin: The Admin archiving it.
            key: Its key.

        Returns:
            The case.

        Raises:
            EvalCaseNotFoundError: If no case has the key.
        """
        stored = self.get_case(key)
        if not stored.case.archived:
            self._cases.update(
                key,
                stored.case.content,
                archived=True,
                now=self._clock.now(),
                admin_id=admin.id,
            )
        return self.get_case(key)

    def add_image(self, file_name: str, content: bytes, media_type: str) -> EvalImage:
        """Keep an uploaded test image under a new name, for a case to send.

        A new name each time means a stored image never changes, so old runs
        still show the image they used.

        Args:
            file_name: The uploaded file's name.
            content: The file.
            media_type: Its type, e.g. image/png.

        Returns:
            The image, with the name cases refer to it by.

        Raises:
            InvalidEvalImageError: If it isn't a PNG, JPEG or WebP, or is
                over 5 MB.
        """
        suffix = IMAGE_MEDIA_TYPES.get(media_type)
        if suffix is None or not content or len(content) > IMAGE_MAX_BYTES:
            raise InvalidEvalImageError()
        image = EvalImage(
            name=f"{image_name_stem(file_name)}-{uuid4().hex[:8]}{suffix}",
            content=content,
            media_type=media_type,
        )
        self._images.add_missing([image], self._clock.now())
        return image

    def get_image(self, name: str) -> EvalImage:
        """Read a test image, to show it beside its case.

        Args:
            name: Its name.

        Returns:
            The image.

        Raises:
            EvalImageNotFoundError: If no image has the name.
        """
        found = self._images.get_many([name])
        if not found:
            raise EvalImageNotFoundError()
        return found[0]

    def _key_problems(self, key: str) -> dict[str, str]:
        """Check a new case's key.

        Args:
            key: The key.

        Returns:
            A message for the `key` field; empty when it fits.
        """
        if not CASE_KEY.match(key) or len(key) > CASE_KEY_MAX_LENGTH:
            return {
                "key": "Use lowercase letters, numbers and single hyphens, at "
                f"most {CASE_KEY_MAX_LENGTH} characters, e.g. reminded-of-sister."
            }
        return {}

    def _content_problems(self, case: EvalCase) -> dict[str, str]:
        """Check a case's content against its Eval's shape and checks.

        Args:
            case: The case.

        Returns:
            A message per field path; empty when it fits.
        """
        shape = CASE_SHAPES[case.eval]
        problems = find_problems(shape, case.content)
        if problems:
            return problems
        try:
            read_case(case)
        except InvalidEvalCaseError as error:
            return error.field_errors()
        except (KeyError, ValueError, TypeError) as error:
            return {"": f"The case can't be read: {error}"}
        images = image_fields(shape, case.content)
        stored = {image.name for image in self._images.get_many(list(images.values()))}
        return {
            path: "This image isn't stored; upload it again."
            for path, name in images.items()
            if name not in stored
        }
