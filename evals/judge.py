import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from companion.core.models import ChatLine, ChatRole
from companion.core.ports import ChatModel

JUDGE_MODEL = "deepseek-chat"
NO_VERSION = "none"
CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")

PERSONA_JUDGE_INSTRUCTIONS = """\
You judge replies written by Zeph, an AI companion people talk to on Telegram.
You are given a conversation and some rules. For each rule, decide whether
Zeph's replies in the whole conversation keep it. Judge only what Zeph wrote,
not the person. Be strict: one reply that breaks a rule fails that rule.

Answer with JSON only, in exactly this shape, one verdict per rule:
{"verdicts": [{"rule": "<rule id>", "passed": true, "reason": "<one sentence>"}]}"""

VERSION_JUDGE_INSTRUCTIONS = """\
You check which version of a document an AI companion's reply draws on. You
are given the person's question, the reply and several versions of the
document, each with a name. The versions differ in their details (numbers,
colours, names, steps). Decide which one version the reply's details come
from. If the reply draws on none of them, or you can't tell, answer "none".

Answer with JSON only, in exactly this shape:
{"version": "<version name or none>", "reason": "<one sentence naming the details>"}"""


@dataclass(frozen=True)
class RuleVerdict:
    """The judge's verdict on one Persona rule for one conversation.

    Attributes:
        rule: The rule's ID.
        passed: Whether the replies kept the rule.
        reason: Why, in the judge's words.
    """

    rule: str
    passed: bool
    reason: str


@dataclass(frozen=True)
class VersionVerdict:
    """Which version of a document a reply draws on.

    Attributes:
        version: The version's name, or "none".
        reason: Why, in the judge's words.
    """

    version: str
    reason: str


def read_json_answer(answer: str) -> dict[str, Any]:
    """Read the judge's answer as a JSON object, with or without a code fence.

    Args:
        answer: The judge's answer.

    Returns:
        The JSON object.

    Raises:
        ValueError: If the answer isn't a JSON object.
    """
    content = json.loads(CODE_FENCE.sub("", answer.strip()))
    if not isinstance(content, dict):
        raise ValueError("The answer is not a JSON object")
    return content


def read_rule_verdicts(answer: str, rules: Sequence[str]) -> list[RuleVerdict]:
    """Read the judge's verdict on each rule it was asked about.

    A rule the judge skipped, or every rule when the answer can't be read,
    fails, so a confused judge never hides a broken rule.

    Args:
        answer: The judge's answer.
        rules: The IDs of the rules it was asked about.

    Returns:
        One verdict per rule, in the order asked.
    """
    try:
        verdicts = read_json_answer(answer)["verdicts"]
        given = {
            str(verdict["rule"]): RuleVerdict(
                rule=str(verdict["rule"]),
                passed=verdict["passed"] is True,
                reason=str(verdict["reason"]),
            )
            for verdict in verdicts
        }
    except (ValueError, KeyError, TypeError):
        reason = f"The judge's answer could not be read: {answer}"
        return [RuleVerdict(rule=rule, passed=False, reason=reason) for rule in rules]
    return [
        given.get(rule, RuleVerdict(rule, False, "The judge gave no verdict."))
        for rule in rules
    ]


def read_version_verdict(answer: str, versions: Sequence[str]) -> VersionVerdict:
    """Read which version the judge says a reply draws on.

    Args:
        answer: The judge's answer.
        versions: The names of the versions it was shown.

    Returns:
        The verdict; "none" when the answer names no known version or can't
        be read.
    """
    try:
        content = read_json_answer(answer)
        version = str(content["version"]).strip().lower()
        reason = str(content["reason"])
    except (ValueError, KeyError, TypeError):
        return VersionVerdict(
            NO_VERSION, f"The judge's answer could not be read: {answer}"
        )
    return VersionVerdict(version if version in versions else NO_VERSION, reason)


def judge_persona_rules(
    chat_model: ChatModel, transcript: str, rules: Mapping[str, str]
) -> list[RuleVerdict]:
    """Ask the judge whether a conversation's replies keep each rule.

    Args:
        chat_model: The model that judges.
        transcript: The conversation, one "Person:" or "Zeph:" line each.
        rules: Each rule's ID and what it checks.

    Returns:
        One verdict per rule, in the order given.
    """
    rule_lines = "\n".join(f"- {rule}: {check}" for rule, check in rules.items())
    question = f"Rules:\n{rule_lines}\n\nConversation:\n{transcript}"
    answer = chat_model.generate(
        model=JUDGE_MODEL,
        instructions=PERSONA_JUDGE_INSTRUCTIONS,
        history=[ChatLine(role=ChatRole.USER, text=question)],
    )
    return read_rule_verdicts(answer.text, list(rules))


def judge_version(
    chat_model: ChatModel, question: str, reply: str, versions: Mapping[str, str]
) -> VersionVerdict:
    """Ask the judge which version of a document a reply draws on.

    Args:
        chat_model: The model that judges.
        question: What the person asked.
        reply: The Companion's reply.
        versions: Each version's name and content.

    Returns:
        The verdict.
    """
    version_parts = "\n\n".join(
        f"Version “{name}”:\n{content}" for name, content in versions.items()
    )
    prompt = f"Question:\n{question}\n\nReply:\n{reply}\n\n{version_parts}"
    answer = chat_model.generate(
        model=JUDGE_MODEL,
        instructions=VERSION_JUDGE_INSTRUCTIONS,
        history=[ChatLine(role=ChatRole.USER, text=prompt)],
    )
    return read_version_verdict(answer.text, list(versions))
