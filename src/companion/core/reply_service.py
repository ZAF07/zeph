from concurrent.futures import ThreadPoolExecutor

from companion.core.conversations import ConversationService, ReplyPartlySentError
from companion.core.curiosities import CuriosityRaiser
from companion.core.knowledge_retrieval import KnowledgeRetrieval
from companion.core.life_threads import ThreadReminder
from companion.core.memory_retrieval import MemoryRetrieval
from companion.core.models import MessageToAnswer, UserSnapshot
from companion.core.move_outcomes import MoveOutcomeFinder
from companion.core.reply_gate import ReplyGate, Stopped
from companion.core.response_composition import ResponseComposer
from companion.core.understanding import UnderstandingService, may_send_photo
from companion.core.woven_check_ins import WovenCheckInOffer, WovenCheckIns


class ReplyService:
    """Answers a connected User's Message, one step after another (ADR-0009).

    The steps run in this order: the ReplyGate applies the house rules left
    once the Message's texts are saved and checked, then the Companion is
    reminded of the User's Life Threads the Message touches and lists the
    Curiosities whose day has come and finds the User's past Move Outcomes
    closest to the Message, then the Understanding works out what the User
    needs and which Moves to make, which User Memory matters, which Threads
    and Curiosities to bring up and which Knowledge documents fit, then that
    memory, any older Conversations it asked to look up and passages from
    the Knowledge documents it chose are recalled, while the Check-in model
    decides whether to offer the reply a Check-in that is due, then the
    reply is composed, in its strict priority order, and delivered, and the
    Threads and Curiosities it brought up are marked raised. A struggling
    User is offered none of their Shared Photos back unless they asked for
    one. Every step reads the User from the same snapshot.
    """

    def __init__(
        self,
        reply_gate: ReplyGate,
        conversations: ConversationService,
        thread_reminder: ThreadReminder,
        curiosity_raiser: CuriosityRaiser,
        move_outcome_finder: MoveOutcomeFinder,
        understanding: UnderstandingService,
        memory_retrieval: MemoryRetrieval,
        knowledge_retrieval: KnowledgeRetrieval,
        response_composer: ResponseComposer,
        woven_check_ins: WovenCheckIns,
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
            understanding: Works out what the User needs before each reply.
            memory_retrieval: Reads the User Memory and picks out what the
                Understanding chose.
            knowledge_retrieval: Finds passages in the Knowledge documents the
                Understanding chose.
            response_composer: Writes the Companion's reply.
            woven_check_ins: Lets the reply weave in a Check-in that is due.
        """
        self._reply_gate = reply_gate
        self._conversations = conversations
        self._thread_reminder = thread_reminder
        self._curiosity_raiser = curiosity_raiser
        self._move_outcome_finder = move_outcome_finder
        self._understanding = understanding
        self._memory_retrieval = memory_retrieval
        self._knowledge_retrieval = knowledge_retrieval
        self._response_composer = response_composer
        self._woven_check_ins = woven_check_ins

    def handle(self, message: MessageToAnswer, snapshot: UserSnapshot) -> None:
        """Answer one screened Message: apply the house rules, then reply if needed.

        When the ReplyGate stops the reply nothing is composed. A failing
        step raises, so the caller can send its fallback message. A due
        Check-in is offered to the reply as an optional extra. One the reply
        leaves out, or offered to a reply that fails before any of it is
        sent, is taken back, so it stays due; once part of a reply that
        brought it up is sent, it counts as sent and is never woven in again.

        Args:
            message: The Message to answer, its texts already saved and
                checked by the Safeguard.
            snapshot: The User who sent it, read once as the reply starts.
        """
        gate_result = self._reply_gate.check(message, snapshot)
        if isinstance(gate_result, Stopped):
            return
        saved_memory = self._memory_retrieval.read(snapshot)
        reminded = self._thread_reminder.remind(snapshot, message.conversation_id)
        due = self._curiosity_raiser.due(snapshot, message.conversation_id)
        move_outcomes = self._move_outcome_finder.find(
            snapshot, message.conversation_id
        )
        understood = self._understanding.understand(
            snapshot,
            message.conversation_id,
            saved_memory,
            reminded,
            due,
            move_outcomes,
        )
        form = understood.understanding.form
        with ThreadPoolExecutor(max_workers=1) as executor:
            deciding = executor.submit(
                self._woven_check_ins.decide,
                snapshot,
                message.conversation_id,
                form,
                saved_memory,
                reminded,
                understood.asks_a_question,
            )
            memory = self._memory_retrieval.recall(
                snapshot, saved_memory, form.memory_categories, form.look_up_past
            )
            knowledge = self._knowledge_retrieval.recall(snapshot, form.knowledge)
            woven = deciding.result()
        woven_check_in = (
            self._woven_check_ins.save(snapshot, woven) if woven is not None else None
        )
        check_in_offer = (
            WovenCheckInOffer(woven, woven_check_in)
            if woven is not None and woven_check_in is not None
            else None
        )
        try:
            reply = self._response_composer.compose(
                message.conversation_id,
                snapshot,
                memory.text,
                knowledge,
                guidance=understood.reply_guidance,
                optional_offers=(
                    [check_in_offer.offer] if check_in_offer is not None else []
                ),
                data_deletion_note=gate_result.data_deletion_note,
                shared_photo_ids=(
                    memory.shared_photo_ids if may_send_photo(form) else ()
                ),
            )
            if check_in_offer is not None and not check_in_offer.was_brought_up:
                self._take_back(snapshot, check_in_offer)
                check_in_offer = None
            self._conversations.deliver_reply(
                message.user_id,
                message.conversation_id,
                message.chat_id,
                reply.parts,
                snapshot.settings,
                reply.sticker.id if reply.sticker else None,
                reply.shared_photo.id if reply.shared_photo else None,
            )
        except ReplyPartlySentError:
            raise
        except Exception:
            if check_in_offer is not None:
                self._take_back(snapshot, check_in_offer)
            raise
        self._thread_reminder.mark_raised(message.conversation_id, form.bring_up)
        self._curiosity_raiser.mark_raised(message.conversation_id, form.curiosities)

    def _take_back(self, snapshot: UserSnapshot, offer: WovenCheckInOffer) -> None:
        """Take back the Woven-in Check-in offered to a reply, so it stays due.

        Args:
            snapshot: The User being answered, as read for the reply.
            offer: The Check-in offered to the reply, with its saved row.
        """
        self._woven_check_ins.take_back(snapshot, offer.woven, offer.check_in)
