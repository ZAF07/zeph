import pytest

from companion.adapters.chat_tools import (
    holds_tool_call_markup,
    without_tool_call_markup,
)

SEEN_IN_EVAL_RUN = (
    "<tool call>\n\n<function=change_directness>\n"
    "<parameter=directness>direct</parameter>\n</function>\n</tool_call>"
)


@pytest.mark.parametrize(
    "text",
    [
        SEEN_IN_EVAL_RUN,
        "<tool call>",
        "<tool_call>",
        "</tool_call>",
        '<tool_call>{"name": "change_directness"}</tool_call>',
        "<function=change_directness>",
        "sure, one sec\n\n<function=pause_check_ins></function>",
        "<parameter=directness>direct</parameter>",
        '<function_calls><invoke name="web_search"></invoke></function_calls>',
        "<｜tool▁calls▁begin｜>change_directness<｜tool▁calls▁end｜>",
        "<TOOL_CALL>",
    ],
)
def test_text_with_a_tool_call_written_out_holds_markup(text: str) -> None:
    assert holds_tool_call_markup(text)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Done, I'll be more direct from now on.",
        "that's a tough call <3",
        "if a < b and b > c then fine",
        "the function of a tool is to help you call your mum",
        "I'd call that a <big> step",
    ],
)
def test_ordinary_text_holds_no_markup(text: str) -> None:
    assert not holds_tool_call_markup(text)


def test_a_reply_that_was_only_a_tool_call_is_left_empty() -> None:
    assert without_tool_call_markup(SEEN_IN_EVAL_RUN) == ""


def test_the_words_around_a_tool_call_are_kept() -> None:
    text = (
        "Got it, straight talk it is.\n\n"
        "<function=change_directness>\n<parameter=directness>direct</parameter>\n"
        "</function>\n\nWhat's on your mind?"
    )

    assert without_tool_call_markup(text) == (
        "Got it, straight talk it is.\n\n\n\nWhat's on your mind?"
    )


def test_a_tool_call_that_never_closes_is_cut_to_the_end() -> None:
    text = "On it.\n\n<function=change_directness>\n<parameter=directness>direct"

    assert without_tool_call_markup(text) == "On it."


def test_a_closing_tag_left_on_its_own_is_taken_out() -> None:
    assert without_tool_call_markup("All set.\n</tool_call>") == "All set."


def test_ordinary_text_is_left_as_it_is() -> None:
    assert without_tool_call_markup("a < b, and <3 to you") == "a < b, and <3 to you"
