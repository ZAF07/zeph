from companion.core.conversations import ConversationService, ReplyPartlySentError
from companion.core.curiosities import CuriosityRaiser
from companion.core.knowledge_retrieval import KnowledgeRetrieval
from companion.core.life_threads import ThreadReminder
from companion.core.memory_retrieval import MemoryRetrieval
from companion.core.models import MessageToAnswer, UserSnapshot
from companion.core.move_outcomes import MoveOutcomeFinder
from companion.core.patterns import PatternReminder
from companion.core.recent_messages import RecentMessagesReader
from companion.core.reply_attempt import ReplyAttempt
from companion.core.reply_gate import ReplyGate, Stopped
from companion.core.reply_plan import ReplyPlanService
from companion.core.reply_tools import ReplyOffer
from companion.core.response_composition import ResponseComposer
from companion.core.understanding import UnderstandingService
from companion.core.woven_check_ins import (
    WovenCheckIns,
    format_woven_check_in_for_reply,
)


class ReplyService:
    """Answers a connected User's Message, one step after another (ADR-0009).

    The steps run in this order (ADR-0021): the ReplyGate applies the house
    rules left once the Message's texts are saved and checked, then the
    Recent Messages are read (every message from the last hours, across
    Conversations), which the Understanding, Reply Plan and reply all see;
    then the Understanding reads what the User said, means, feels and
    wants, deciding nothing; then the Companion is reminded of the User's
    Life Threads the Message touches and the Patterns linked to them or
    close to it, lists the Curiosities whose day has come and finds the
    User's past Move Outcomes closest to the Message;
    then the Reply Plan
    decides what the User needs and which Moves to make, which User Memory
    matters, which Threads and Curiosities to bring up, which Knowledge
    documents fit and, when code allows a due Check-in, whether one of its
    Kinds fits; then that memory, any older Conversations the Understanding
    asked to look up and passages from the Knowledge documents the Reply
    Plan chose are recalled; then the reply is composed, in its strict
    priority order, a small check asks whether it brought up the Check-in
    it was offered, and it is delivered, and the Threads and Curiosities it
    brought up are marked raised. A struggling User is
    offered none of their Shared Photos back unless they asked for one.
    Every step reads the User from the same snapshot.
    """

    def __init__(
        self,
        reply_gate: ReplyGate,
        conversations: ConversationService,
        thread_reminder: ThreadReminder,
        curiosity_raiser: CuriosityRaiser,
        move_outcome_finder: MoveOutcomeFinder,
        understanding: UnderstandingService,
        reply_plan: ReplyPlanService,
        memory_retrieval: MemoryRetrieval,
        knowledge_retrieval: KnowledgeRetrieval,
        response_composer: ResponseComposer,
        woven_check_ins: WovenCheckIns,
        recent_messages: RecentMessagesReader,
        pattern_reminder: PatternReminder,
    ) -> None:
        """Set up the service.

        Args:
            reply_gate: Applies the house rules to each Message.
            conversations: Sends composed replies.
            thread_reminder: Finds the Life Threads each Message touches and
                marks those brought up.
            curiosity_raiser: Lists the Curiosities whose day has come and
                marks those brought up.
            move_outcome_finder: Finds the User's past Move Outcomes that fit
                each Message.
            understanding: Reads each Message before the reply is planned.
            reply_plan: Decides what each reply does.
            memory_retrieval: Reads the User Memory and picks out what the
                Reply Plan chose.
            knowledge_retrieval: Finds passages in the Knowledge documents the
                Reply Plan chose.
            response_composer: Writes the Companion's reply.
            woven_check_ins: Says which Check-in Kinds the Reply Plan may
                weave in, and saves, checks and takes back the one it chose.
            recent_messages: Reads the messages every step of the reply sees.
            pattern_reminder: Finds the Patterns that come to mind for each
                Message.
        """
        self._reply_gate = reply_gate
        self._conversations = conversations
        self._thread_reminder = thread_reminder
        self._curiosity_raiser = curiosity_raiser
        self._move_outcome_finder = move_outcome_finder
        self._understanding = understanding
        self._reply_plan = reply_plan
        self._memory_retrieval = memory_retrieval
        self._knowledge_retrieval = knowledge_retrieval
        self._response_composer = response_composer
        self._woven_check_ins = woven_check_ins
        self._recent_messages = recent_messages
        self._pattern_reminder = pattern_reminder

    def handle(
        self, message: MessageToAnswer, snapshot: UserSnapshot, attempt: ReplyAttempt
    ) -> None:
        """Answer one screened Message: apply the house rules, then reply if needed.

        When the ReplyGate stops the reply nothing is composed. The house
        rules are skipped when an earlier try at the Message passed them. A
        failing step raises, so the caller can send its fallback message; so
        does a try a new text dropped before any of it was sent. A due
        Check-in the Reply Plan chose is offered to the reply as an optional
        extra. One the brought-up check finds the reply left out, or offered
        to a reply that fails or is dropped before any of it is sent, is
        taken back, so it stays due; once part of a reply that brought it up
        is sent, it counts as sent and is never woven in again.

        Args:
            message: The Message to answer, its texts already saved and
                checked by the Safeguard.
            snapshot: The User who sent it, read once as the reply starts.
            attempt: This try at the Message, which a new text may drop.

        Raises:
            ReplyDroppedError: If a new text dropped the try before any of
                the reply was sent.
        """
        gate_result = attempt.apply_house_rules(
            lambda: self._reply_gate.check(message, snapshot)
        )
        if isinstance(gate_result, Stopped):
            return
        saved_memory = self._memory_retrieval.read(snapshot)
        recent = self._recent_messages.read(snapshot, message.conversation_id)
        understanding = self._understanding.understand(
            snapshot, recent, saved_memory.portrait
        )
        attempt.raise_if_dropped()
        reminded = self._thread_reminder.remind(
            snapshot, message.conversation_id, understanding.form.means
        )
        patterns = self._pattern_reminder.remind(
            snapshot, message.conversation_id, understanding.form.means, reminded
        )
        due = self._curiosity_raiser.due(
            snapshot, message.conversation_id, understanding.form.struggling
        )
        move_outcomes = self._move_outcome_finder.find(
            snapshot, message.conversation_id
        )
        planned = self._reply_plan.plan(
            snapshot,
            understanding,
            recent,
            saved_memory,
            reminded,
            due,
            move_outcomes,
            self._woven_check_ins.kinds_to_offer(snapshot, understanding.form),
            patterns,
        )
        plan = planned.reply_plan.form
        attempt.raise_if_dropped()
        memory = self._memory_retrieval.recall(
            snapshot,
            saved_memory,
            plan.memory_categories,
            understanding.form.look_up_past,
        )
        knowledge = self._knowledge_retrieval.recall(snapshot, plan.knowledge)
        offered = (
            self._woven_check_ins.save(snapshot, planned.check_in)
            if planned.check_in is not None
            else None
        )
        try:
            attempt.raise_if_dropped()
            reply = self._response_composer.compose(
                recent,
                snapshot,
                memory.text,
                knowledge,
                guidance=planned.reply_guidance,
                optional_offers=(
                    [
                        ReplyOffer(
                            instructions=format_woven_check_in_for_reply(offered.woven)
                        )
                    ]
                    if offered is not None
                    else []
                ),
                data_deletion_note=gate_result.data_deletion_note,
                shared_photo_ids=(
                    memory.shared_photo_ids if planned.may_send_photo else ()
                ),
            )
            if offered is not None and not self._woven_check_ins.was_brought_up(
                snapshot, offered.woven, reply.texts
            ):
                self._woven_check_ins.take_back(snapshot, offered)
                offered = None
            self._conversations.deliver_reply(
                message.user_id,
                message.conversation_id,
                message.chat_id,
                reply.parts,
                snapshot.settings,
                reply.sticker.id if reply.sticker else None,
                reply.shared_photo.id if reply.shared_photo else None,
                before_sending=attempt.start_sending,
            )
        except ReplyPartlySentError:
            raise
        except Exception:
            if offered is not None:
                self._woven_check_ins.take_back(snapshot, offered)
            raise
        self._thread_reminder.mark_raised(message.conversation_id, plan.bring_up)
        self._curiosity_raiser.mark_raised(message.conversation_id, plan.curiosities)
