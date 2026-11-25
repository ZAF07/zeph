import json
import logging
import random
import time
from collections.abc import Callable, Sequence
from enum import StrEnum

from companion.core.chat_settings import CLAIM_CHECK_PROMPT
from companion.core.curiosities import ASKED_CHECK_PROMPT
from companion.core.models import ChatLine, ModelAnswer, PhotoImage, PlatformSettings
from companion.core.platform_settings import (
    CHECK_IN_PROMPT,
    CURIOSITY_KEEPING_PROMPT,
    KNOWLEDGE_WHEN_IT_HELPS_PROMPT,
    LIFE_THREAD_KEEPING_PROMPT,
    MEMORY_PROCESSING_PROMPT,
    MOVE_OUTCOME_KEEPING_PROMPT,
    PATTERN_KEEPING_PROMPT,
    PATTERN_TAGGING_PROMPT,
    PERSONAL_STICKER_KEEPING_PROMPT,
    PORTRAIT_PROMPT,
    REPLY_PLAN_PROMPT,
    SAFEGUARD_PROMPT,
    UNDERSTANDING_PROMPT,
)
from companion.core.ports import ChatTool, Repositories
from companion.core.woven_check_ins import BROUGHT_UP_CHECK_PROMPT

logger = logging.getLogger(__name__)

SHORTEST_WAIT_SECONDS = 3.0
LONGEST_WAIT_SECONDS = 8.0
TOKENS_PER_CALL = 100
ANSWERED_CALL_LOG_PREFIX = "Load test: answered a "
CANNED_REPLY = "That sounds like a lot. What part of it is weighing on you most?"
CANNED_PORTRAIT = "Someone busy at work who likes to talk things through."
CANNED_WHEN_IT_HELPS = "When someone wants a calm, steady practice."
CANNED_PHOTO_DESCRIPTION = "A photo of a mug of tea on a wooden table."
CANNED_CHECK_IN = "hey, just thinking of you. how's today going?"
FALLBACK_NEED = "Be heard"


class CallShape(StrEnum):
    """Which of the app's model calls a call is, told apart by its instructions."""

    SAFEGUARD = "safeguard"
    UNDERSTANDING = "understanding"
    REPLY_PLAN = "reply plan"
    REPLY = "reply"
    CHECK_IN = "check-in"
    BROUGHT_UP_CHECK = "brought-up check"
    SETTINGS_CLAIM_CHECK = "settings claim check"
    CURIOSITY_ASKED_CHECK = "curiosity asked check"
    CONVERSATION_END = "conversation end"
    LIFE_THREADS = "life threads"
    PATTERN_TAGGING = "pattern tagging"
    PATTERNS = "patterns"
    CURIOSITIES = "curiosities"
    MOVE_OUTCOMES = "move outcomes"
    PORTRAIT = "portrait"
    PERSONAL_STICKERS = "personal stickers"
    KNOWLEDGE_WHEN_IT_HELPS = "knowledge when it helps"


def random_wait() -> float:
    """Pick how long a fake model call takes, like a real model's speed.

    Returns:
        A number of seconds between 3 and 8.
    """
    return random.uniform(SHORTEST_WAIT_SECONDS, LONGEST_WAIT_SECONDS)


def shape_of(instructions: str, settings: PlatformSettings) -> CallShape:
    """Tell which model call this is, from the prompts in Platform settings.

    Most calls use one prompt as their whole instructions. The Reply Plan
    ends with its prompt after the Outlook, and a Check-in with its prompt
    after the Persona. Anything else is a reply.

    Args:
        instructions: The call's instructions.
        settings: The Platform settings the app read its prompts from.

    Returns:
        The call's shape.
    """
    whole_prompts = {
        settings.get(SAFEGUARD_PROMPT): CallShape.SAFEGUARD,
        settings.get(UNDERSTANDING_PROMPT): CallShape.UNDERSTANDING,
        settings.get(MEMORY_PROCESSING_PROMPT): CallShape.CONVERSATION_END,
        settings.get(LIFE_THREAD_KEEPING_PROMPT): CallShape.LIFE_THREADS,
        settings.get(PATTERN_TAGGING_PROMPT): CallShape.PATTERN_TAGGING,
        settings.get(PATTERN_KEEPING_PROMPT): CallShape.PATTERNS,
        settings.get(CURIOSITY_KEEPING_PROMPT): CallShape.CURIOSITIES,
        settings.get(MOVE_OUTCOME_KEEPING_PROMPT): CallShape.MOVE_OUTCOMES,
        settings.get(PORTRAIT_PROMPT): CallShape.PORTRAIT,
        settings.get(PERSONAL_STICKER_KEEPING_PROMPT): CallShape.PERSONAL_STICKERS,
        settings.get(KNOWLEDGE_WHEN_IT_HELPS_PROMPT): (
            CallShape.KNOWLEDGE_WHEN_IT_HELPS
        ),
        BROUGHT_UP_CHECK_PROMPT: CallShape.BROUGHT_UP_CHECK,
        CLAIM_CHECK_PROMPT: CallShape.SETTINGS_CLAIM_CHECK,
        ASKED_CHECK_PROMPT: CallShape.CURIOSITY_ASKED_CHECK,
    }
    if instructions in whole_prompts:
        return whole_prompts[instructions]
    reply_plan_prompt = settings.get(REPLY_PLAN_PROMPT)
    if reply_plan_prompt and instructions.endswith(reply_plan_prompt):
        return CallShape.REPLY_PLAN
    check_in_prompt = settings.get(CHECK_IN_PROMPT)
    if check_in_prompt and instructions.endswith(check_in_prompt):
        return CallShape.CHECK_IN
    return CallShape.REPLY


def understanding_answer() -> str:
    """Write an Understanding form for an ordinary, calm Message.

    Returns:
        The form as JSON.
    """
    no_view = {"said": "", "read": "", "unclear": ""}
    return json.dumps(
        {
            "said": "They talked about their day.",
            "means": "They want to talk about how their day went.",
            "feelings": no_view,
            "mood": "tired",
            "intensity": "low",
            "wants": no_view,
            "cause_known": True,
            "struggling": False,
            "asked_for_photo": False,
            "look_up_past": [],
        }
    )


def reply_plan_answer(need: str) -> str:
    """Write a Reply Plan form that listens, with no extras picked.

    Args:
        need: The Need to pick; one Admins have set.

    Returns:
        The form as JSON.
    """
    return json.dumps(
        {
            "where_we_are": "They are telling me about their day.",
            "read": "",
            "say_read": False,
            "need": need,
            "guidance": "Listen and ask one open question.",
            "lead_move": None,
            "support_move": None,
            "next_move": None,
            "memory_categories": [],
            "threads_touched": [],
            "bring_up": [],
            "left_alone": [],
            "knowledge": None,
            "send_photo": False,
            "check_in": None,
            "patterns_used": [],
            "offer_pattern": None,
        }
    )


def conversation_end_answer() -> str:
    """Write a Day Summary with no Memory Items or photos to keep.

    Returns:
        The answer as JSON.
    """
    return json.dumps(
        {
            "summary": "A busy day at work that left them tired.",
            "mood": "tired",
            "offered": "Listened and asked what weighed on them most.",
            "memory_operations": [],
            "photos_to_keep": [],
        }
    )


class LoadTestChatModel:
    """Chat model for load tests: waits like a real model, makes no network call.

    Each call waits a random 3 to 8 seconds, then answers in the shape the
    app expects for that call: a risk label for the Safeguard, a form for
    the Understanding and Reply Plan, a Check-in decision, empty lists for
    the Conversation-end keeping steps, and a short reply otherwise. The
    call is told apart by comparing its instructions with the prompts in
    Platform settings, read again on each call, so Admin edits still match.
    """

    def __init__(
        self,
        repositories: Repositories,
        wait: Callable[[], float] = random_wait,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Set up the model.

        Args:
            repositories: Where the prompts, Needs and Check-in Kinds are read.
            wait: Picks how many seconds each call takes.
            sleep: Waits that long.
        """
        self._repositories = repositories
        self._wait = wait
        self._sleep = sleep

    def generate(
        self,
        model: str,
        thinking: bool,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
        message_instructions: str = "",
    ) -> ModelAnswer:
        """Wait, then give a canned answer that fits the call.

        Args:
            model: The model asked for; not used.
            thinking: Whether thinking was asked for; not used.
            instructions: The call's instructions, which tell its shape.
            history: The call's history; a Check-in's lists its Kinds.
            tools: The tools offered; never called.
            message_instructions: The instructions made for this one call;
                not used.

        Returns:
            The canned answer.
        """
        shape = shape_of(instructions, self._repositories.platform_settings.load())
        self._sleep(self._wait())
        logger.info("%s%s call", ANSWERED_CALL_LOG_PREFIX, shape)
        return ModelAnswer(
            text=self._answer(shape, history),
            tokens_in=TOKENS_PER_CALL,
            tokens_out=TOKENS_PER_CALL,
        )

    def _answer(self, shape: CallShape, history: list[ChatLine]) -> str:
        """Write the canned answer for a call's shape.

        Args:
            shape: The call's shape.
            history: The call's history.

        Returns:
            The answer's text.
        """
        match shape:
            case CallShape.SAFEGUARD:
                return "none"
            case CallShape.UNDERSTANDING:
                return understanding_answer()
            case CallShape.REPLY_PLAN:
                return reply_plan_answer(self._first_need())
            case CallShape.CHECK_IN:
                return self._check_in_answer(history)
            case CallShape.BROUGHT_UP_CHECK | CallShape.SETTINGS_CLAIM_CHECK:
                return "no"
            case CallShape.CURIOSITY_ASKED_CHECK:
                return "yes"
            case CallShape.CONVERSATION_END:
                return conversation_end_answer()
            case CallShape.LIFE_THREADS:
                return json.dumps({"threads": []})
            case CallShape.PATTERN_TAGGING:
                return json.dumps({"observations": []})
            case CallShape.PATTERNS:
                return json.dumps({"patterns": []})
            case CallShape.CURIOSITIES:
                return json.dumps({"curiosities": []})
            case CallShape.MOVE_OUTCOMES:
                return json.dumps({"move_outcomes": []})
            case CallShape.PERSONAL_STICKERS:
                return json.dumps({"stickers_to_keep": []})
            case CallShape.PORTRAIT:
                return CANNED_PORTRAIT
            case CallShape.KNOWLEDGE_WHEN_IT_HELPS:
                return CANNED_WHEN_IT_HELPS
            case CallShape.REPLY:
                return CANNED_REPLY

    def _first_need(self) -> str:
        """Name the first Need Admins set, for the Reply Plan to pick.

        Returns:
            Its name; a stock one when there are none.
        """
        needs = self._repositories.needs.list_all()
        return needs[0].name if needs else FALLBACK_NEED

    def _check_in_answer(self, history: list[ChatLine]) -> str:
        """Send the first Kind offered that needs no Shared Photo or Curiosity.

        Args:
            history: The Check-in call's history, which lists the Kinds offered.

        Returns:
            A send decision, or a skip when no such Kind was offered.
        """
        description = "\n".join(line.text for line in history)
        offered = [
            kind
            for kind in self._repositories.check_ins.list_kinds()
            if f"- {kind.name}:" in description and not kind.has_fixed_behaviour
        ]
        if not offered:
            return json.dumps({"decision": "skip", "reason": "No plain Kind offered."})
        return json.dumps(
            {"decision": "send", "kind": offered[0].name, "message": CANNED_CHECK_IN}
        )


class LoadTestPhotoViewer:
    """Photo viewer for load tests: waits like a real model, then describes a mug."""

    def __init__(
        self,
        wait: Callable[[], float] = random_wait,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Set up the viewer.

        Args:
            wait: Picks how many seconds each look takes.
            sleep: Waits that long.
        """
        self._wait = wait
        self._sleep = sleep

    def look(
        self, model: str, thinking: bool, instructions: str, photo: PhotoImage
    ) -> ModelAnswer:
        """Wait, then describe the photo the same way every time.

        Args:
            model: The model asked for; not used.
            thinking: Whether thinking was asked for; not used.
            instructions: What to write; not used.
            photo: The photo; not looked at.

        Returns:
            The canned description.
        """
        self._sleep(self._wait())
        logger.info("Load test: looked at a photo")
        return ModelAnswer(
            text=CANNED_PHOTO_DESCRIPTION,
            tokens_in=TOKENS_PER_CALL,
            tokens_out=TOKENS_PER_CALL,
        )
