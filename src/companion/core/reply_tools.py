from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from companion.core.models import (
    LibrarySticker,
    PersonalSticker,
    SharedPhoto,
    UserSnapshot,
)
from companion.core.ports import ChatTool

Attachment = LibrarySticker | PersonalSticker | SharedPhoto


@dataclass(frozen=True)
class ReplyContext:
    """What a reply is answering, beyond the User, for picking its tools.

    Attributes:
        conversation_id: The Conversation being replied in.
        shared_photo_ids: The User's Shared Photos that matter for the
            message, which the reply may send one of; empty if none.
    """

    conversation_id: UUID
    shared_photo_ids: Sequence[UUID] = ()


@dataclass
class ReplyOffer:
    """The tools one provider offers a reply, and what they picked.

    Attributes:
        tools: The tools the reply may call; empty when none fit.
        instructions: What to add to the reply's instructions; "" if nothing.
        picked: The sticker or Shared Photo a tool picked while the reply was
            written, to send after its text; None until one is picked.
        closing_text: A fixed text a tool asked to send, word for word, as
            the last text message of the reply; "" if none.
    """

    tools: list[ChatTool] = field(default_factory=list)
    instructions: str = ""
    picked: Attachment | None = None
    closing_text: str = ""


class ReplyToolProvider(Protocol):
    """Offers a reply the tools of one Feature, when it works for the User."""

    def offer(self, snapshot: UserSnapshot, context: ReplyContext) -> ReplyOffer:
        """Pick the tools and instructions for one reply.

        Args:
            snapshot: The User being replied to.
            context: What the reply is answering.

        Returns:
            The offer; an empty one when the Feature doesn't work for them.
        """
        ...
