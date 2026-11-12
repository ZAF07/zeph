from collections.abc import Sequence
from dataclasses import replace
from typing import Any

from companion.core.models import ChatLine, ModelAnswer
from companion.core.ports import ChatModel, ChatTool
from evals.report import EvalReport


class TokenCountingChatModel:
    """Chat model that adds the tokens of every answer to the eval report.

    It also notes the name of every tool the model calls, in
    `called_tools`, so an eval can check which tools a reply used.
    """

    def __init__(self, chat_model: ChatModel, report: EvalReport) -> None:
        """Wrap a chat model.

        Args:
            chat_model: The real chat model.
            report: Where the tokens are added up.
        """
        self._chat_model = chat_model
        self._report = report
        self.called_tools: list[str] = []

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
        recorded_tools = [self._recording(tool) for tool in tools]
        answer = self._chat_model.generate(model, instructions, history, recorded_tools)
        self._report.tokens_in += answer.tokens_in
        self._report.tokens_out += answer.tokens_out
        return answer

    def _recording(self, tool: ChatTool) -> ChatTool:
        """Wrap a tool so each call to it is noted in `called_tools`.

        Args:
            tool: The tool.

        Returns:
            The same tool, noting its name before it runs.
        """

        def run(arguments: dict[str, Any]) -> str:
            """Note the call, then run the tool.

            Args:
                arguments: The model's arguments.

            Returns:
                What the tool returns.
            """
            self.called_tools.append(tool.name)
            return tool.run(arguments)

        return replace(tool, run=run)
