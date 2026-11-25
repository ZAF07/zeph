from companion.adapters.evals.stand_ins import CountingChatModel, TokenCounter
from companion.core.models import ChatLine, ChatRole
from tests.fakes import ScriptedChatModel


def test_the_two_instructions_reach_the_real_chat_model_apart() -> None:
    real_chat_model = ScriptedChatModel()
    real_chat_model.script("hey")
    chat_model = CountingChatModel(real_chat_model, TokenCounter())

    chat_model.generate(
        model="anthropic/claude-haiku-5.5",
        thinking=False,
        instructions="Be Zeph.",
        history=[ChatLine(role=ChatRole.USER, text="hi")],
        message_instructions="They just asked about work.",
    )

    [call] = real_chat_model.calls
    assert call.fixed_instructions == "Be Zeph."
    assert call.message_instructions == "They just asked about work."
