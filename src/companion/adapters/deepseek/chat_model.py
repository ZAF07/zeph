import logging
from collections.abc import Callable, Sequence

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr

from companion.adapters.chat_tools import (
    MAX_TOOL_ROUNDS,
    broken_arguments_message,
    to_tool_schema,
    unknown_tool_message,
)
from companion.core.models import ChatLine, ChatRole, ModelAnswer, ToolCallRecord
from companion.core.ports import ChatTool

logger = logging.getLogger(__name__)

CURRENT_MODEL = "deepseek-flash"
OLD_CHAT_MODEL = "deepseek-chat"
OLD_REASONER_MODEL = "deepseek-reasoner"
DIRECT_NAMES_BY_OPENROUTER_NAME = {
    "deepseek/deepseek-v4.1-flash-1017": "deepseek-flash",
    "deepseek/deepseek-v4-pro-0813": "deepseek-v4-pro",
}

AskModel = Callable[[list[BaseMessage]], AIMessage]


class UnsupportedModelError(ValueError):
    """Raised when direct DeepSeek is asked for a model it can't call."""


def to_direct_name(model: str) -> str:
    """Turn a model name saved in Platform Settings into DeepSeek's own name.

    Saved names are OpenRouter names (e.g. "deepseek/deepseek-v4.1-flash-1017").
    A name with no provider part is taken to be a direct DeepSeek name
    already and is kept as it is.

    Args:
        model: The saved model name.

    Returns:
        The name direct DeepSeek knows the model by.

    Raises:
        UnsupportedModelError: If the name is another provider's model, or a
            DeepSeek model with no known direct name.
    """
    if "/" not in model:
        return model
    direct_name = DIRECT_NAMES_BY_OPENROUTER_NAME.get(model)
    if direct_name is None:
        raise UnsupportedModelError(
            f"Direct DeepSeek can't call {model}. Pick a DeepSeek model in "
            "Prompts and models, or set CHAT_MODEL_ADAPTER to an adapter "
            "that can call it."
        )
    return direct_name


def build_client(api_key: str, model: str, thinking: bool) -> ChatDeepSeek:
    """Set up a DeepSeek client for one call, with thinking on or off.

    An OpenRouter DeepSeek name is sent as its direct DeepSeek name. The old
    names still work: "deepseek-chat" is sent as the current model
    with thinking as asked, and "deepseek-reasoner" as the current model
    with thinking always on, warning when it was asked to think less.

    Args:
        api_key: The DeepSeek API key.
        model: The model to use, e.g. "deepseek/deepseek-v4.1-flash-1017".
        thinking: Whether the model should think before it answers.

    Returns:
        The client.

    Raises:
        UnsupportedModelError: If direct DeepSeek can't call the model.
    """
    direct_model = to_direct_name(model)
    if direct_model == OLD_REASONER_MODEL:
        if not thinking:
            logger.warning(
                "deepseek-reasoner always thinks; thinking stays on for this call"
            )
        thinking = True
    if direct_model in (OLD_CHAT_MODEL, OLD_REASONER_MODEL):
        direct_model = CURRENT_MODEL
    return ChatDeepSeek(
        model_name=direct_model,
        api_key=SecretStr(api_key),
        timeout=60,
        extra_body={"thinking": {"type": "enabled" if thinking else "disabled"}},
    )


def to_langchain_messages(
    instructions: str, history: list[ChatLine]
) -> list[BaseMessage]:
    """Turn instructions and Conversation history into LangChain messages.

    Args:
        instructions: What the model should be and do.
        history: The Conversation so far, oldest first.

    Returns:
        A system message followed by one message per history line.
    """
    messages: list[BaseMessage] = [SystemMessage(instructions)]
    for line in history:
        if line.role == ChatRole.USER:
            messages.append(HumanMessage(line.text))
        else:
            messages.append(AIMessage(line.text))
    return messages


def to_model_answer(
    text: str,
    responses: Sequence[AIMessage],
    tool_calls: Sequence[ToolCallRecord] = (),
) -> ModelAnswer:
    """Put the reply text together with the tokens, tool calls and reasoning.

    Args:
        text: The reply text.
        responses: Every response the model gave on the way to the reply.
        tool_calls: The tool calls made on the way, with their results.

    Returns:
        The answer; a response with no usage counts as no tokens, and the
        reasoning is None when no response had any.
    """
    usages = [response.usage_metadata for response in responses]
    tokens_in = sum(usage["input_tokens"] for usage in usages if usage)
    tokens_out = sum(usage["output_tokens"] for usage in usages if usage)
    reasonings = [
        str(response.additional_kwargs["reasoning_content"])
        for response in responses
        if response.additional_kwargs.get("reasoning_content")
    ]
    return ModelAnswer(
        text=text,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        tool_calls=tuple(tool_calls),
        reasoning="\n\n".join(reasonings) if reasonings else None,
    )


def answer_with_tools(
    ask: AskModel,
    ask_without_tools: AskModel,
    messages: list[BaseMessage],
    tools: Sequence[ChatTool],
) -> ModelAnswer:
    """Let the model call tools, sending back each result, until it replies.

    A call whose arguments are not valid JSON is sent back as an error so
    the model can try again. After `MAX_TOOL_ROUNDS` rounds of tool calls
    the model must reply without calling any more.

    Args:
        ask: Asks the model, with the tools bound, for its next message.
        ask_without_tools: Asks the same model, told not to call tools.
        messages: The messages so far; tool calls and results are added.
        tools: The tools the model may call.

    Returns:
        The reply text, the tokens every round took and every tool call made;
        a broken call's arguments are kept as given, under "raw".
    """
    tools_by_name = {tool.name: tool for tool in tools}
    responses: list[AIMessage] = []
    tool_calls: list[ToolCallRecord] = []
    for _ in range(MAX_TOOL_ROUNDS):
        response = ask(messages)
        responses.append(response)
        if not response.tool_calls and not response.invalid_tool_calls:
            return to_model_answer(response.text, responses, tool_calls)
        messages.append(response)
        for broken_call in response.invalid_tool_calls:
            name = broken_call["name"] or ""
            result = broken_arguments_message(name)
            messages.append(ToolMessage(result, tool_call_id=broken_call["id"] or ""))
            tool_calls.append(
                ToolCallRecord(name, {"raw": broken_call["args"]}, result)
            )
        for tool_call in response.tool_calls:
            tool = tools_by_name.get(tool_call["name"])
            result = (
                tool.run(tool_call["args"])
                if tool
                else unknown_tool_message(tool_call["name"])
            )
            messages.append(ToolMessage(result, tool_call_id=tool_call["id"]))
            tool_calls.append(
                ToolCallRecord(tool_call["name"], tool_call["args"], result)
            )
    final_response = ask_without_tools(messages)
    return to_model_answer(
        final_response.text, [*responses, final_response], tool_calls
    )


class DeepSeekChatModel:
    """Generates text with DeepSeek through LangChain's chat-model interface."""

    def __init__(self, api_key: str) -> None:
        """Set up the adapter.

        Args:
            api_key: The DeepSeek API key.
        """
        self._api_key = api_key

    def generate(
        self,
        model: str,
        thinking: bool,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> ModelAnswer:
        """Generate the next reply, calling tools first if the model wants to.

        Args:
            model: The model to use, e.g. "deepseek/deepseek-v4.1-flash-1017".
            thinking: Whether the model should think before it answers.
            instructions: What the model should be and do (Persona and prompt).
            history: The Conversation so far, oldest first.
            tools: The tools the model may call; none by default.

        Returns:
            The reply text and the tokens it took.
        """
        client = build_client(self._api_key, model, thinking)
        messages = to_langchain_messages(instructions, history)
        if not tools:
            response = client.invoke(messages)
            return to_model_answer(response.text, [response])
        schemas = [to_tool_schema(tool) for tool in tools]
        return answer_with_tools(
            client.bind_tools(schemas).invoke,
            client.bind_tools(schemas, tool_choice="none").invoke,
            messages,
            tools,
        )
