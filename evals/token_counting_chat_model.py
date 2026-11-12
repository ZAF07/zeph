from collections.abc import Sequence

from companion.core.models import ChatLine, ModelAnswer
from companion.core.ports import ChatModel, ChatTool
from evals.report import EvalReport


class TokenCountingChatModel:
    """Chat model that adds the tokens of every answer to the eval report."""

    def __init__(self, chat_model: ChatModel, report: EvalReport) -> None:
        """Wrap a chat model.

        Args:
            chat_model: The real chat model.
            report: Where the tokens are added up.
        """
        self._chat_model = chat_model
        self._report = report

    def generate(
        self,
        model: str,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> ModelAnswer:
        """Generate an answer with the real chat model and count its tokens.

        Args:
            model: The model to use.
            instructions: What the model should be and do.
            history: The conversation so far, oldest first.
            tools: The tools the model may call.

        Returns:
            The real chat model's answer.
        """
        answer = self._chat_model.generate(model, instructions, history, tools)
        self._report.tokens_in += answer.tokens_in
        self._report.tokens_out += answer.tokens_out
        return answer
