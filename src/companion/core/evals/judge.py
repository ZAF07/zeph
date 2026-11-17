import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from companion.core.evals.case_shapes import (
    ChoiceOption,
    FieldKind,
    FormShape,
    ShapeField,
    ShapeSection,
    long_text_field,
)
from companion.core.models import ChatLine, ChatRole
from companion.core.ports import ChatModel

NO_VERSION = "none"
CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$")


@dataclass(frozen=True)
class JudgeSettings:
    """The Judge's model, thinking and prompts, set by Admins (ADR-0004).

    Attributes:
        model: The model that judges.
        thinking: Whether it thinks before it answers.
        persona_instructions: Its prompt for checking replies against rules.
        version_instructions: Its prompt for telling which version of a
            Knowledge Document a reply draws on.
        outcome_instructions: Its prompt for checking a kept Move Outcome
            against rules.
    """

    model: str
    thinking: bool
    persona_instructions: str
    version_instructions: str
    outcome_instructions: str

    @classmethod
    def from_values(cls, values: Mapping[str, Any]) -> "JudgeSettings":
        """Read the settings from their stored values.

        Args:
            values: Each setting's value by name.

        Returns:
            The settings.
        """
        return cls(
            model=values["model"],
            thinking=values["thinking"],
            persona_instructions=values["persona_instructions"],
            version_instructions=values["version_instructions"],
            outcome_instructions=values["outcome_instructions"],
        )


def judge_shape(model_choices: Sequence[str]) -> FormShape:
    """Describe the Judge's settings as a form, the way case forms are.

    Args:
        model_choices: The models Admins can pick.

    Returns:
        The shape, which checks a save and draws the form.
    """
    return FormShape(
        [
            ShapeSection(
                "Model",
                "The model that marks Persona, Knowledge, Understanding and "
                "Move Outcome cases. Every Variant in a run is marked by the "
                "same Judge.",
                [
                    ShapeField(
                        "model",
                        "Model",
                        "The model the Judge asks. A stronger model marks more "
                        "reliably but costs more per case.",
                        FieldKind.CHOICE,
                        required=True,
                        options=[ChoiceOption(name, name) for name in model_choices],
                    ),
                    ShapeField(
                        "thinking",
                        "Thinking",
                        "Whether the Judge thinks before it answers. On is "
                        "slower and uses more tokens.",
                        FieldKind.ON_OFF,
                        default=False,
                    ),
                ],
            ),
            ShapeSection(
                "Prompts",
                "What the Judge is told. A change applies from the next run; "
                "runs already done keep the Judge they used.",
                [
                    long_text_field(
                        "persona_instructions",
                        "Rules prompt",
                        "How the Judge checks replies against a case's rules "
                        "(Persona and Understanding). It must ask for JSON "
                        'like {"verdicts": [{"rule", "passed", "reason"}]}, or '
                        "every rule fails as unreadable.",
                    ),
                    long_text_field(
                        "version_instructions",
                        "Versions prompt",
                        "How the Judge tells which version of a Knowledge "
                        "Document a reply draws on (Knowledge). It must ask "
                        'for JSON like {"version", "reason"}.',
                    ),
                    long_text_field(
                        "outcome_instructions",
                        "Move Outcomes prompt",
                        "How the Judge checks a kept Move Outcome's situation, "
                        "feeling and why against a case's rules (Move Outcome). "
                        'It must ask for JSON like {"verdicts": [{"rule", '
                        '"passed", "reason"}]}, or every rule fails as '
                        "unreadable.",
                    ),
                ],
            ),
        ]
    )


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
    chat_model: ChatModel,
    judge: JudgeSettings,
    transcript: str,
    rules: Mapping[str, str],
) -> list[RuleVerdict]:
    """Ask the judge whether a conversation's replies keep each rule.

    Args:
        chat_model: The model that judges.
        judge: The Judge's model, thinking and prompts.
        transcript: The conversation, one "Person:" or "Zeph:" line each.
        rules: Each rule's ID and what it checks.

    Returns:
        One verdict per rule, in the order given.
    """
    return ask_about_rules(
        chat_model,
        judge,
        judge.persona_instructions,
        f"{rule_lines(rules)}\n\nConversation:\n{transcript}",
        rules,
    )


def rule_lines(rules: Mapping[str, str]) -> str:
    """Write rules as the Judge is shown them.

    Args:
        rules: Each rule's ID and what it checks.

    Returns:
        "Rules:" then one "- <id>: <check>" line per rule.
    """
    lines = "\n".join(f"- {rule}: {check}" for rule, check in rules.items())
    return f"Rules:\n{lines}"


def ask_about_rules(
    chat_model: ChatModel,
    judge: JudgeSettings,
    instructions: str,
    question: str,
    rules: Mapping[str, str],
) -> list[RuleVerdict]:
    """Ask the judge for a verdict on each rule, with one of its prompts.

    Args:
        chat_model: The model that judges.
        judge: The Judge's model and thinking.
        instructions: The Judge's prompt for this kind of check.
        question: The rules and what they are checked on.
        rules: Each rule's ID and what it checks.

    Returns:
        One verdict per rule, in the order given.
    """
    answer = chat_model.generate(
        model=judge.model,
        thinking=judge.thinking,
        instructions=instructions,
        history=[ChatLine(role=ChatRole.USER, text=question)],
    )
    return read_rule_verdicts(answer.text, list(rules))


def judge_version(
    chat_model: ChatModel,
    judge: JudgeSettings,
    question: str,
    reply: str,
    versions: Mapping[str, str],
) -> VersionVerdict:
    """Ask the judge which version of a document a reply draws on.

    Args:
        chat_model: The model that judges.
        judge: The Judge's model, thinking and prompts.
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
        model=judge.model,
        thinking=judge.thinking,
        instructions=judge.version_instructions,
        history=[ChatLine(role=ChatRole.USER, text=prompt)],
    )
    return read_version_verdict(answer.text, list(versions))


def judge_move_outcome_rules(
    chat_model: ChatModel,
    judge: JudgeSettings,
    transcript: str,
    outcome: str,
    rules: Mapping[str, str],
) -> list[RuleVerdict]:
    """Ask the judge whether a kept Move Outcome keeps each rule.

    Args:
        chat_model: The model that judges.
        judge: The Judge's model, thinking and prompts.
        transcript: The Conversation, one "Person:" or "Zeph:" line each.
        outcome: The Move Outcome kept, as one line.
        rules: Each rule's ID and what it checks.

    Returns:
        One verdict per rule, in the order given.
    """
    return ask_about_rules(
        chat_model,
        judge,
        judge.outcome_instructions,
        f"{rule_lines(rules)}\n\nConversation:\n{transcript}\n\n"
        f"Move Outcome kept:\n{outcome}",
        rules,
    )
