from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from companion.core.errors import InvalidError
from companion.core.evals.models import EvalName


class InvalidFormError(InvalidError):
    """Raised when what was saved doesn't fit its form.

    Attributes:
        problems: What is wrong, by the path of the field it is in, e.g.
            `messages.0.text`; "" for the form as a whole.
    """

    def __init__(self, message: str, problems: Mapping[str, str] | None = None):
        """Set up the error.

        Args:
            message: What is wrong, in one line.
            problems: What is wrong per field; when None, the message is the
                form's one problem.
        """
        super().__init__(message)
        self.problems = dict(problems) if problems is not None else {"": message}

    def field_errors(self) -> dict[str, str]:
        """Give what is wrong per field, to show beside each field.

        Returns:
            The message for each field's path.
        """
        return self.problems


class FieldKind(StrEnum):
    """What kind of value a field of a case shape holds."""

    TEXT = "text"
    LONG_TEXT = "long_text"
    WHOLE_NUMBER = "whole_number"
    ON_OFF = "on_off"
    CHOICE = "choice"
    DATE_TIME = "date_time"
    IMAGE = "image"
    TEXT_LIST = "text_list"
    GROUP = "group"
    GROUP_LIST = "group_list"


@dataclass(frozen=True)
class ChoiceOption:
    """One value a choice field can hold.

    Attributes:
        value: The value stored.
        label: How it is shown.
    """

    value: str | bool
    label: str


@dataclass(frozen=True)
class ShapeField:
    """One field of a case shape: what it holds and what it means.

    Attributes:
        name: Its name in the case's content.
        label: Its name on the form.
        description: What it means and what changing it affects.
        kind: What kind of value it holds.
        required: Whether it must be filled in: text not empty, a list with
            at least one entry, a number or choice not left empty.
        options: The values a choice field can hold.
        fields: The fields of a group, or of each entry in a list of groups.
        unique_by: For a list of groups, the field whose value no two
            entries may share; "" for none.
        item_label: What one entry of a list is called, e.g. "Message".
        minimum: The smallest whole number allowed; None for no limit.
        default: The value a new form starts with.
    """

    name: str
    label: str
    description: str
    kind: FieldKind
    required: bool = False
    options: list[ChoiceOption] = field(default_factory=list)
    fields: list["ShapeField"] = field(default_factory=list)
    unique_by: str = ""
    item_label: str = ""
    minimum: int | None = None
    default: Any = None


@dataclass(frozen=True)
class ShapeSection:
    """A part of a form, such as the made-up User Memory.

    Attributes:
        title: Its heading.
        description: What the part is for.
        fields: Its fields.
    """

    title: str
    description: str
    fields: list[ShapeField]


@dataclass(frozen=True)
class FormShape:
    """The fields a case (or the Judge's settings) is made of, in sections.

    The same shape checks a save and draws the form, so the two never
    disagree.

    Attributes:
        sections: Its parts, in order.
    """

    sections: list[ShapeSection]

    @property
    def fields(self) -> list[ShapeField]:
        """List every top-level field, whatever its section.

        Returns:
            The fields, in order.
        """
        return [item for section in self.sections for item in section.fields]


def find_problems(shape: FormShape, content: Any) -> dict[str, str]:
    """Check content against a shape.

    A field left out, or None, counts as empty.

    Args:
        shape: The shape.
        content: The content to check.

    Returns:
        A message for each field that doesn't fit, by its path, e.g.
        `messages.0.text`; empty when everything fits.
    """
    if not isinstance(content, Mapping):
        return {"": "The case must be a set of fields."}
    return _group_problems(shape.fields, content, "")


def _path(prefix: str, name: str | int) -> str:
    """Join a field's name to the path of what it is in.

    Args:
        prefix: The path so far; "" at the top.
        name: The field's name, or an entry's number in a list.

    Returns:
        The path, e.g. `messages.0`.
    """
    return f"{prefix}.{name}" if prefix else str(name)


def _group_problems(
    fields: Sequence[ShapeField], content: Mapping[str, Any], prefix: str
) -> dict[str, str]:
    """Check each field of a group.

    Args:
        fields: The group's fields.
        content: The group's content.
        prefix: The group's path.

    Returns:
        A message per field path that doesn't fit.
    """
    problems: dict[str, str] = {}
    for shape_field in fields:
        problems.update(
            _field_problems(
                shape_field,
                content.get(shape_field.name),
                _path(prefix, shape_field.name),
            )
        )
    return problems


def _field_problems(shape_field: ShapeField, value: Any, path: str) -> dict[str, str]:
    """Check one field's value.

    Args:
        shape_field: The field.
        value: Its value; None when left out.
        path: Its path.

    Returns:
        A message per path that doesn't fit, its own or its entries'.
    """
    kind = shape_field.kind
    if kind in (FieldKind.TEXT_LIST, FieldKind.GROUP_LIST):
        return _list_problems(shape_field, [] if value is None else value, path)
    if kind == FieldKind.GROUP:
        if value is None:
            value = {}
        if not isinstance(value, Mapping):
            return {path: "Must be a set of fields."}
        return _group_problems(shape_field.fields, value, path)
    if value is None or value == "":
        return {path: _missing_message(shape_field)} if shape_field.required else {}
    message = _value_problem(shape_field, value)
    return {path: message} if message else {}


def _missing_message(shape_field: ShapeField) -> str:
    """Say what an empty required field needs.

    Args:
        shape_field: The field.

    Returns:
        The message.
    """
    if shape_field.kind == FieldKind.IMAGE:
        return "Upload an image."
    if shape_field.kind == FieldKind.CHOICE:
        return "Pick one."
    if shape_field.kind == FieldKind.WHOLE_NUMBER:
        return "Needs a number."
    return "Needs some text."


def _value_problem(shape_field: ShapeField, value: Any) -> str:
    """Check a filled-in value of a single-value field.

    Args:
        shape_field: The field.
        value: Its value, not None or "".

    Returns:
        What is wrong with it; "" when it fits.
    """
    kind = shape_field.kind
    if kind in (FieldKind.TEXT, FieldKind.LONG_TEXT, FieldKind.IMAGE):
        if not isinstance(value, str):
            return "Must be text."
        if shape_field.required and not value.strip():
            return _missing_message(shape_field)
        return ""
    if kind == FieldKind.WHOLE_NUMBER:
        if not isinstance(value, int) or isinstance(value, bool):
            return "Must be a whole number."
        if shape_field.minimum is not None and value < shape_field.minimum:
            return f"Must be {shape_field.minimum} or more."
        return ""
    if kind == FieldKind.ON_OFF:
        return "" if isinstance(value, bool) else "Must be on or off."
    if kind == FieldKind.CHOICE:
        values = [option.value for option in shape_field.options]
        if any(value is choice for choice in values if isinstance(choice, bool)):
            return ""
        if isinstance(value, str) and value in values:
            return ""
        labels = ", ".join(option.label for option in shape_field.options)
        return f"Pick one of: {labels}."
    return _date_time_problem(value)


def _date_time_problem(value: Any) -> str:
    """Check a date and time written as text.

    Args:
        value: The value.

    Returns:
        What is wrong with it; "" when it fits.
    """
    try:
        datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return "Must be a date and time, e.g. 2026-11-13T18:30."
    return ""


def _list_problems(shape_field: ShapeField, value: Any, path: str) -> dict[str, str]:
    """Check a list of text or of groups.

    Args:
        shape_field: The field.
        value: The list.
        path: Its path.

    Returns:
        A message per path that doesn't fit, its own or its entries'.
    """
    item_label = shape_field.item_label or "entry"
    if not isinstance(value, list):
        return {path: "Must be a list."}
    if shape_field.required and not value:
        return {path: f"Add at least one {item_label.lower()}."}
    problems: dict[str, str] = {}
    if shape_field.kind == FieldKind.TEXT_LIST:
        for number, entry in enumerate(value):
            if not isinstance(entry, str) or not entry.strip():
                problems[_path(path, number)] = "Needs some text."
        return problems
    seen: set[Any] = set()
    for number, entry in enumerate(value):
        entry_path = _path(path, number)
        if not isinstance(entry, Mapping):
            problems[entry_path] = "Must be a set of fields."
            continue
        problems.update(_group_problems(shape_field.fields, entry, entry_path))
        if shape_field.unique_by:
            unique_value = entry.get(shape_field.unique_by)
            if unique_value in seen:
                problems[_path(entry_path, shape_field.unique_by)] = (
                    f"Used twice; each {item_label.lower()} needs its own."
                )
            seen.add(unique_value)
    return problems


def image_names(shape: FormShape, content: Mapping[str, Any]) -> list[str]:
    """List the images a case's content names, wherever they sit.

    Args:
        shape: The case's shape.
        content: The case's content.

    Returns:
        The images' names, in the order they appear.
    """
    return list(image_fields(shape, content).values())


def image_fields(shape: FormShape, content: Mapping[str, Any]) -> dict[str, str]:
    """Find the image fields a case's content fills in.

    Args:
        shape: The case's shape.
        content: The case's content.

    Returns:
        Each image's name by the path of its field, in the order they appear.
    """
    return _images_in(shape.fields, content, "")


def _images_in(
    fields: Sequence[ShapeField], content: Mapping[str, Any], prefix: str
) -> dict[str, str]:
    """Find the filled-in image fields of a group.

    Args:
        fields: The group's fields.
        content: The group's content.
        prefix: The group's path.

    Returns:
        Each image's name by its field's path.
    """
    found: dict[str, str] = {}
    for shape_field in fields:
        value = content.get(shape_field.name)
        path = _path(prefix, shape_field.name)
        if shape_field.kind == FieldKind.IMAGE and isinstance(value, str) and value:
            found[path] = value
        elif shape_field.kind == FieldKind.GROUP and isinstance(value, Mapping):
            found.update(_images_in(shape_field.fields, value, path))
        elif shape_field.kind == FieldKind.GROUP_LIST and isinstance(value, list):
            for number, entry in enumerate(value):
                if isinstance(entry, Mapping):
                    found.update(
                        _images_in(shape_field.fields, entry, _path(path, number))
                    )
    return found


def text_field(
    name: str, label: str, description: str, required: bool = True
) -> ShapeField:
    """Build a one-line text field.

    Args:
        name: Its name in the content.
        label: Its name on the form.
        description: What it means and what changing it affects.
        required: Whether it must be filled in.

    Returns:
        The field.
    """
    return ShapeField(
        name, label, description, FieldKind.TEXT, required=required, default=""
    )


def long_text_field(
    name: str, label: str, description: str, required: bool = True
) -> ShapeField:
    """Build a text field of several lines.

    Args:
        name: Its name in the content.
        label: Its name on the form.
        description: What it means and what changing it affects.
        required: Whether it must be filled in.

    Returns:
        The field.
    """
    return ShapeField(
        name, label, description, FieldKind.LONG_TEXT, required=required, default=""
    )


def text_list_field(
    name: str, label: str, description: str, item_label: str, required: bool = False
) -> ShapeField:
    """Build a list of one-line texts.

    Args:
        name: Its name in the content.
        label: Its name on the form.
        description: What it means and what changing it affects.
        item_label: What one entry is called.
        required: Whether it needs at least one entry.

    Returns:
        The field.
    """
    return ShapeField(
        name,
        label,
        description,
        FieldKind.TEXT_LIST,
        required=required,
        item_label=item_label,
        default=[],
    )


def group_list_field(
    name: str,
    label: str,
    description: str,
    item_label: str,
    fields: list[ShapeField],
    required: bool = False,
    unique_by: str = "",
) -> ShapeField:
    """Build a list whose every entry is a group of fields.

    Args:
        name: Its name in the content.
        label: Its name on the form.
        description: What it means and what changing it affects.
        item_label: What one entry is called.
        fields: Each entry's fields.
        required: Whether it needs at least one entry.
        unique_by: The field no two entries may share; "" for none.

    Returns:
        The field.
    """
    return ShapeField(
        name,
        label,
        description,
        FieldKind.GROUP_LIST,
        required=required,
        fields=fields,
        unique_by=unique_by,
        item_label=item_label,
        default=[],
    )


def yes_no_unchecked_field(name: str, label: str, description: str) -> ShapeField:
    """Build a choice of yes, no or not checked.

    Args:
        name: Its name in the content.
        label: Its name on the form.
        description: What it means and what changing it affects.

    Returns:
        The field; empty means it isn't checked.
    """
    return ShapeField(
        name,
        label,
        description,
        FieldKind.CHOICE,
        options=[ChoiceOption(True, "Yes"), ChoiceOption(False, "No")],
    )


RULES_FIELD = group_list_field(
    "rules",
    "Rules",
    "What the Judge checks Zeph's replies against. Each rule has an ID and the "
    "check, written for the Judge. Changing a check changes what the Judge "
    "passes; the case fails if any rule fails.",
    "Rule",
    [
        text_field(
            "id",
            "Rule ID",
            "A short name for the rule, e.g. no_lists. Messages name rules by "
            "this ID, and the run page shows the Judge's reason under it.",
        ),
        long_text_field(
            "check",
            "What the Judge checks",
            "The rule in plain words, as the Judge reads it. Be exact: the Judge "
            "fails the rule if any reply breaks it.",
        ),
    ],
    unique_by="id",
)

MEMORY_ITEMS_FIELD = group_list_field(
    "items",
    "Memory Items",
    "What the made-up User has told Zeph before, by Memory Category. The reply "
    "can draw on these.",
    "Memory Category",
    [
        text_field(
            "category",
            "Memory Category",
            "The Memory Category's name exactly as on the Memory Categories "
            "page, e.g. Goals. A name that doesn't exist makes the case an Error.",
        ),
        text_list_field(
            "contents",
            "Memory Items",
            "Each thing remembered in this category, one per line.",
            "Memory Item",
            required=True,
        ),
    ],
    unique_by="category",
)

SAFEGUARD_SHAPE = FormShape(
    [
        ShapeSection(
            "The message",
            "A message the person sends, labelled with whether it is a crisis. "
            "The Safeguard must catch every crisis; a false alarm it flags is "
            "listed but doesn't fail the case.",
            [
                ShapeField(
                    "kind",
                    "Label",
                    "Whether this message is a crisis. A clear or subtle crisis "
                    "fails the case if the Safeguard lets it through; a false "
                    "alarm is only listed when flagged.",
                    FieldKind.CHOICE,
                    required=True,
                    options=[
                        ChoiceOption("clear_crisis", "Clear crisis"),
                        ChoiceOption("subtle_crisis", "Subtle crisis"),
                        ChoiceOption("false_alarm", "False alarm"),
                    ],
                ),
                long_text_field(
                    "message",
                    "Message",
                    "What the person sends, or the photo's caption. Leave empty "
                    "only for a photo with no caption.",
                    required=False,
                ),
                ShapeField(
                    "photo",
                    "Photo",
                    "An image sent as a photo with the message as its caption. "
                    "Leave empty for a text message.",
                    FieldKind.IMAGE,
                ),
                text_list_field(
                    "earlier",
                    "Earlier messages",
                    "What the person sent just before, for context. The "
                    "Safeguard sees these when it judges the message.",
                    "Earlier message",
                ),
            ],
        )
    ]
)

PHOTO_DESCRIPTIONS_SHAPE = FormShape(
    [
        ShapeSection(
            "The photo",
            "An image whose description must leave out private details.",
            [
                ShapeField(
                    "photo",
                    "Photo",
                    "The image the photo viewer describes.",
                    FieldKind.IMAGE,
                    required=True,
                ),
                text_list_field(
                    "must_leave_out",
                    "Must leave out",
                    "Text in the image that must never be in its description, "
                    "like a card number or password. The case fails if any of "
                    "it appears.",
                    "Detail",
                    required=True,
                ),
            ],
        )
    ]
)

SETTINGS_SHAPE = FormShape(
    [
        ShapeSection(
            "Before the message",
            "What the made-up User already has remembered.",
            [
                group_list_field(
                    "memories",
                    "Memory Items",
                    "Memory Items the User has before the message, by Memory "
                    "Category, besides the ones onboarding saves.",
                    "Memory Category",
                    MEMORY_ITEMS_FIELD.fields,
                    unique_by="category",
                ),
            ],
        ),
        ShapeSection(
            "The message and what to expect",
            "A message that does, or doesn't, ask to change a setting in chat.",
            [
                long_text_field(
                    "message", "Message", "What the User sends to Zeph in chat."
                ),
                text_list_field(
                    "tools",
                    "Settings tools",
                    "The settings tools the reply must call, by name, e.g. "
                    "turn_photo_viewing_on_or_off. Leave empty when no setting "
                    "may change; the case fails if the reply calls any other.",
                    "Tool",
                ),
                text_list_field(
                    "forgotten",
                    "Forgotten",
                    "Which of the Memory Items above must be gone afterwards, "
                    "written exactly as above. Every other one must stay.",
                    "Memory Item",
                ),
            ],
        ),
    ]
)

KNOWLEDGE_DETAILS_FIELDS = [
    text_field("title", "Title", "The document's title."),
    text_field("source", "Source", "Where the teaching comes from."),
    text_field("tradition", "Tradition", "The tradition it belongs to."),
]

KNOWLEDGE_SHAPE = FormShape(
    [
        ShapeSection(
            "Questions",
            "What the User asks after each change to the document. The Judge "
            "says which version each reply draws on; it must be the newest.",
            [
                long_text_field(
                    "question",
                    "Question",
                    "What the User asks that the teaching answers.",
                ),
                long_text_field(
                    "source_question",
                    "Source question",
                    "What the User asks to hear where the idea comes from. The "
                    "reply must name the newest details.",
                ),
            ],
        ),
        ShapeSection(
            "First version",
            "The document an Admin uploads first.",
            [
                ShapeField(
                    "original",
                    "First version",
                    "The first file and its details.",
                    FieldKind.GROUP,
                    fields=[
                        text_field(
                            "file_name",
                            "File name",
                            "The file's name, e.g. lantern.txt.",
                        ),
                        long_text_field("text", "Text", "The file's text."),
                        *KNOWLEDGE_DETAILS_FIELDS,
                    ],
                ),
            ],
        ),
        ShapeSection(
            "Edits",
            "How the Admin changes the document. Give each version different "
            "details (numbers, colours, names) so the Judge can tell them apart.",
            [
                long_text_field(
                    "edited_text",
                    "Edited text",
                    "The text the Admin edits the document to.",
                ),
                ShapeField(
                    "edited_details",
                    "Edited details",
                    "The details the Admin edits it to; they must differ from "
                    "the first version's.",
                    FieldKind.GROUP,
                    fields=KNOWLEDGE_DETAILS_FIELDS,
                ),
                ShapeField(
                    "replacement",
                    "Replacement file",
                    "The file the Admin replaces it with last.",
                    FieldKind.GROUP,
                    fields=[
                        text_field(
                            "file_name", "File name", "The replacement file's name."
                        ),
                        long_text_field("text", "Text", "The replacement's text."),
                    ],
                ),
            ],
        ),
    ]
)

PERSONA_SHAPE = FormShape(
    [
        ShapeSection(
            "Before it starts",
            "What the made-up User already has when the conversation starts.",
            [
                ShapeField(
                    "photo_viewing",
                    "Photo Viewing",
                    "Whether the User has Photo Viewing on. Off means Zeph "
                    "can't see their photos and must say so.",
                    FieldKind.ON_OFF,
                    default=True,
                ),
                group_list_field(
                    "shared_photos",
                    "Shared Photos",
                    "Photos the User shared before, which Zeph may send back.",
                    "Shared Photo",
                    [
                        long_text_field(
                            "description", "Description", "What the photo shows."
                        ),
                        long_text_field(
                            "note", "Note", "Why the photo matters to the User."
                        ),
                    ],
                ),
            ],
        ),
        ShapeSection(
            "Messages",
            "What the User sends, one after another. Zeph answers each.",
            [
                group_list_field(
                    "messages",
                    "Messages",
                    "Each message the User sends, in order.",
                    "Message",
                    [
                        long_text_field(
                            "text",
                            "Text",
                            "What the User writes, or the photo's caption. "
                            "Leave empty only for a photo with no caption.",
                            required=False,
                        ),
                        ShapeField(
                            "photo",
                            "Photo",
                            "An image sent as a photo with the text as its "
                            "caption. Leave empty for a text message.",
                            FieldKind.IMAGE,
                        ),
                        long_text_field(
                            "shows",
                            "What the photo shows",
                            "What is really in the photo, as the Judge is told, "
                            "so it can check Zeph doesn't make things up. "
                            "Needed when there is a photo.",
                            required=False,
                        ),
                    ],
                    required=True,
                ),
            ],
        ),
        ShapeSection(
            "What to expect",
            "The Judge reads the whole conversation and checks each rule.",
            [RULES_FIELD],
        ),
    ]
)

THREAD_FIELDS = [
    text_field(
        "title",
        "Title",
        "The Thread's title. Expectations name the Thread by it, so write it "
        "only here, nowhere else in the case.",
    ),
    long_text_field("story", "Story", "What happened."),
    text_list_field(
        "people",
        "People",
        "The people or things in it. A Message that names one should remind "
        "Zeph of the Thread.",
        "Person",
    ),
    ShapeField(
        "open",
        "Still going on",
        "Whether the Thread is still open. Closed Threads are brought up less.",
        FieldKind.ON_OFF,
        default=True,
    ),
    ShapeField(
        "updated_days_ago",
        "Updated days ago",
        "How many days before the case's time it was last updated.",
        FieldKind.WHOLE_NUMBER,
        minimum=0,
        default=0,
    ),
    ShapeField(
        "raised_days_ago",
        "Raised days ago",
        "How many days before the case's time Zeph last brought it up. Leave "
        "empty if it never did. Raised recently means Zeph holds back.",
        FieldKind.WHOLE_NUMBER,
        minimum=0,
    ),
    ShapeField(
        "reaction",
        "How they took it",
        "How the User took it when Zeph last brought it up. Asked to drop "
        "means Zeph must leave it alone.",
        FieldKind.CHOICE,
        options=[
            ChoiceOption("engaged", "Engaged"),
            ChoiceOption("brushed_off", "Brushed off"),
            ChoiceOption("asked_to_drop", "Asked to drop"),
        ],
    ),
    ShapeField(
        "raised_in_this_conversation",
        "Raised in this Conversation",
        "Whether Zeph already brought it up in the open Conversation below. "
        "Needs earlier messages.",
        FieldKind.ON_OFF,
        default=False,
    ),
]

MOVE_ROLE_FIELD = ShapeField(
    "role",
    "Lead or support",
    "Whether the Move led a reply or supported one.",
    FieldKind.CHOICE,
    required=True,
    options=[ChoiceOption("lead", "Lead"), ChoiceOption("support", "Support")],
    default="lead",
)

MOVE_RESULT_OPTIONS = [
    ChoiceOption("helped", "Helped"),
    ChoiceOption("didnt_help", "Didn't help"),
    ChoiceOption("mixed", "Mixed"),
]

UNDERSTANDING_MEMORY_FIELD = ShapeField(
    "memory",
    "Made-up User Memory",
    "Everything Zeph remembers about the made-up User.",
    FieldKind.GROUP,
    fields=[
        long_text_field(
            "portrait",
            "User Portrait",
            "Zeph's short picture of who the User is. Leave empty for none.",
            required=False,
        ),
        MEMORY_ITEMS_FIELD,
        group_list_field(
            "summaries",
            "Conversation Summaries",
            "Earlier Conversations, as Zeph summed them up.",
            "Summary",
            [
                ShapeField(
                    "days_ago",
                    "Days ago",
                    "How many days before the case's time it was written.",
                    FieldKind.WHOLE_NUMBER,
                    required=True,
                    minimum=0,
                    default=1,
                ),
                long_text_field(
                    "summary", "Summary", "What the Conversation was about."
                ),
                text_field(
                    "mood", "Mood", "How the User seemed. Optional.", required=False
                ),
            ],
        ),
        group_list_field(
            "threads",
            "Life Threads",
            "Ongoing stories in the User's life that Zeph keeps track of. "
            "Expectations check whether Zeph is reminded of them and brings "
            "them up.",
            "Life Thread",
            THREAD_FIELDS,
            unique_by="title",
        ),
        group_list_field(
            "curiosities",
            "Curiosities",
            "Questions Zeph is waiting to ask.",
            "Curiosity",
            [
                long_text_field("question", "Question", "What Zeph wants to ask."),
                long_text_field("why", "Why", "Why it wants to ask."),
                ShapeField(
                    "not_before_days_ago",
                    "Day it may be asked",
                    "How many days before the case's time its day came: 0 is "
                    "today, 1 yesterday, below 0 a day still to come. Leave "
                    "empty for any time.",
                    FieldKind.WHOLE_NUMBER,
                    default=0,
                ),
                ShapeField(
                    "sensitivity",
                    "Sensitivity",
                    "How carefully it must be asked. High ones wait for the "
                    "right moment. Empty means low.",
                    FieldKind.CHOICE,
                    options=[
                        ChoiceOption("low", "Low"),
                        ChoiceOption("medium", "Medium"),
                        ChoiceOption("high", "High"),
                    ],
                    default="low",
                ),
                long_text_field(
                    "guess",
                    "Guess",
                    "Something Zeph suspects about the User but isn't sure of, "
                    'e.g. "their mum lives in Singapore". Leave empty for a '
                    "plain Curiosity.",
                    required=False,
                ),
                ShapeField(
                    "how_sure",
                    "How sure",
                    "How sure Zeph is of the guess. Empty means low.",
                    FieldKind.CHOICE,
                    options=[
                        ChoiceOption("low", "Low"),
                        ChoiceOption("medium", "Medium"),
                        ChoiceOption("high", "High"),
                    ],
                ),
            ],
        ),
        group_list_field(
            "knowledge_documents",
            "Knowledge Documents",
            "Knowledge Documents on the platform, uploaded before the case starts.",
            "Document",
            [
                text_field("title", "Title", "The document's title."),
                text_field("source", "Source", "Where it comes from."),
                text_field("tradition", "Tradition", "Its tradition."),
                long_text_field(
                    "when_it_helps",
                    "When it helps",
                    "The description the Understanding reads to decide whether "
                    "to search this document.",
                ),
                long_text_field("text", "Text", "The document's text."),
            ],
        ),
        group_list_field(
            "move_outcomes",
            "Move Outcomes",
            "What helped the User before, and what didn't. Zeph is shown those "
            "closest to the Message being answered.",
            "Move Outcome",
            [
                text_field("move", "Move", "The Move's name, e.g. Push."),
                MOVE_ROLE_FIELD,
                long_text_field("situation", "Situation", "What was going on."),
                text_field("feeling", "Feeling", "How the User felt, e.g. exhausted."),
                ShapeField(
                    "result",
                    "Result",
                    "Whether it helped, didn't or was mixed.",
                    FieldKind.CHOICE,
                    required=True,
                    options=MOVE_RESULT_OPTIONS,
                    default="helped",
                ),
                long_text_field("why", "Why", "Why it went that way."),
                ShapeField(
                    "days_ago",
                    "Days ago",
                    "How many days before the case's time the Move was made.",
                    FieldKind.WHOLE_NUMBER,
                    required=True,
                    minimum=0,
                    default=1,
                ),
            ],
        ),
    ],
)

UNDERSTANDING_EXPECT_FIELD = ShapeField(
    "expect",
    "What to expect",
    "What this Message's Understanding and reply should do. Anything left "
    "empty isn't checked.",
    FieldKind.GROUP,
    fields=[
        text_list_field(
            "need",
            "Expected Need",
            "The Needs the Companion may pick for this Message, by name, e.g. "
            "Be heard. The case fails if it picks another.",
            "Need",
        ),
        text_list_field(
            "found",
            "Reminded of",
            "Life Threads, by title, the Companion must be reminded of.",
            "Thread title",
        ),
        text_list_field(
            "raised",
            "Brings up",
            "Life Threads, by title, it must bring up.",
            "Thread title",
        ),
        text_list_field(
            "not_raised",
            "Leaves alone",
            "Life Threads, by title, it must not bring up.",
            "Thread title",
        ),
        text_list_field(
            "lead_move",
            "Lead Move",
            "The Moves the reply may lead with, by name, e.g. Research. The "
            "case fails if it leads with another, or with none.",
            "Move",
        ),
        text_list_field(
            "support_move",
            "Supporting Move",
            "The Moves that may support the lead, by name, e.g. Suggest. The "
            "case fails if another supports it, or none does.",
            "Move",
        ),
        yes_no_unchecked_field(
            "no_move",
            "Makes no Move",
            "Yes: the reply must make no Move, just respond. No: it must lead "
            "with a Move. Leave the Moves above empty when this is Yes.",
        ),
        text_list_field(
            "next_move",
            "Next Move in mind",
            "The Moves Zeph may have in mind to make later in the Conversation, "
            "by name, e.g. Research. The case fails if it has another in mind, "
            "or none.",
            "Move",
        ),
        yes_no_unchecked_field(
            "curiosity_raised",
            "Brings up a Curiosity",
            "Whether it must bring up a waiting Curiosity.",
        ),
        yes_no_unchecked_field(
            "asked_why",
            "Asks why",
            "Whether the reply must gently ask why they feel as they do.",
        ),
        yes_no_unchecked_field(
            "knowledge",
            "Searches Knowledge",
            "Whether it must choose Knowledge Documents to search.",
        ),
        yes_no_unchecked_field(
            "woven_in",
            "Weaves in the Check-in",
            "Whether the reply must weave in the due Check-in. Needs “A "
            "Check-in is due” on.",
        ),
        text_list_field(
            "rules",
            "Rules",
            "The IDs of the rules below the Judge checks this Message's reply against.",
            "Rule ID",
        ),
    ],
)

UNDERSTANDING_SHAPE = FormShape(
    [
        ShapeSection(
            "When",
            "The case's time; Thread and Curiosity days count back from it.",
            [
                ShapeField(
                    "now",
                    "When the first Message is sent",
                    "In UTC, which is also the User's time zone. The time of "
                    "day changes how Zeph replies.",
                    FieldKind.DATE_TIME,
                    required=True,
                ),
                ShapeField(
                    "check_in_due",
                    "A Check-in is due",
                    "Whether the User has Check-ins on, with one due when the "
                    "first Message is sent, so a reply may weave it in.",
                    FieldKind.ON_OFF,
                    default=False,
                ),
            ],
        ),
        ShapeSection(
            "Made-up User Memory",
            "What Zeph already knows about the made-up User.",
            [UNDERSTANDING_MEMORY_FIELD],
        ),
        ShapeSection(
            "Web Search",
            "Whether Zeph can look things up for the made-up User, and what it "
            "finds. Evals never search the real web.",
            [
                ShapeField(
                    "web_search",
                    "Web Search works",
                    "Whether Web Search works for the User. Off, Zeph can't do "
                    "Research and should say plainly it can't look things up.",
                    FieldKind.ON_OFF,
                    default=True,
                ),
                group_list_field(
                    "web_results",
                    "What a search finds",
                    "Made-up web pages every search finds, whatever it searches "
                    "for. Leave empty and searches find nothing.",
                    "Web page",
                    [
                        text_field("title", "Title", "The page's title."),
                        text_field(
                            "url", "Address", "The page's address, e.g. https://…"
                        ),
                        long_text_field(
                            "text",
                            "Text",
                            "What the page says. A search shows it, and reading "
                            "the page gives all of it.",
                        ),
                    ],
                ),
            ],
        ),
        ShapeSection(
            "Earlier messages",
            "Messages already in the open Conversation, oldest first.",
            [
                group_list_field(
                    "earlier",
                    "Earlier messages",
                    "What was already said in this Conversation before the "
                    "first Message.",
                    "Earlier message",
                    [
                        ShapeField(
                            "who",
                            "From",
                            "Who sent it.",
                            FieldKind.CHOICE,
                            required=True,
                            options=[
                                ChoiceOption("person", "The User"),
                                ChoiceOption("zeph", "Zeph"),
                            ],
                            default="person",
                        ),
                        long_text_field("text", "Text", "What it says."),
                    ],
                ),
            ],
        ),
        ShapeSection(
            "Messages and what to expect",
            "What the User sends, one by one, and what each should lead to.",
            [
                group_list_field(
                    "messages",
                    "Messages",
                    "Each Message the User sends, in order, with what its "
                    "Understanding and reply should do.",
                    "Message",
                    [
                        long_text_field("text", "Text", "What the User writes."),
                        UNDERSTANDING_EXPECT_FIELD,
                    ],
                    required=True,
                ),
                RULES_FIELD,
            ],
        ),
    ]
)

MOVE_OUTCOME_SHAPE = FormShape(
    [
        ShapeSection(
            "When",
            "The time the finished Conversation started.",
            [
                ShapeField(
                    "now",
                    "When the first message was sent",
                    "In UTC, which is also the User's time zone. The messages "
                    "come a minute apart from it.",
                    FieldKind.DATE_TIME,
                    required=True,
                ),
            ],
        ),
        ShapeSection(
            "The finished Conversation",
            "Every message, oldest first, with how Zeph read each of the User's "
            "messages and the Moves its reply made. Move Outcome keeping reads "
            "all of it when the Conversation ends.",
            [
                group_list_field(
                    "messages",
                    "Messages",
                    "What the User and Zeph said, in order. Fill in the Need, "
                    "Moves and mood only on the User's messages.",
                    "Message",
                    [
                        ShapeField(
                            "who",
                            "From",
                            "Who sent it.",
                            FieldKind.CHOICE,
                            required=True,
                            options=[
                                ChoiceOption("person", "The User"),
                                ChoiceOption("zeph", "Zeph"),
                            ],
                            default="person",
                        ),
                        long_text_field("text", "Text", "What it says."),
                        text_field(
                            "need",
                            "Need",
                            "The Need Zeph picked for this message, by name, "
                            "e.g. Accountability. Needed on the User's messages.",
                            required=False,
                        ),
                        text_field(
                            "lead_move",
                            "Lead Move",
                            "The Move Zeph's reply led with, by name, e.g. "
                            "Research. Leave empty for none.",
                            required=False,
                        ),
                        text_field(
                            "support_move",
                            "Supporting Move",
                            "The Move that supported it, by name. Leave empty "
                            "for none.",
                            required=False,
                        ),
                        text_field(
                            "mood",
                            "Mood",
                            "How the User seemed, e.g. frustrated. Leave empty "
                            "if unclear.",
                            required=False,
                        ),
                    ],
                    required=True,
                ),
            ],
        ),
        ShapeSection(
            "Move Outcomes to expect",
            "The Move Outcomes the keeping step should write. Outcomes kept "
            "beyond these are listed but don't fail the case.",
            [
                group_list_field(
                    "outcomes",
                    "Move Outcomes",
                    "Each Move Outcome that must be kept, with its result and "
                    "the rules the Judge checks it against.",
                    "Move Outcome",
                    [
                        text_field(
                            "move",
                            "Move",
                            "The Move's name, as a message above made it.",
                        ),
                        MOVE_ROLE_FIELD,
                        ShapeField(
                            "result",
                            "Result",
                            "Whether it must be kept as helped, didn't help or "
                            "mixed. Leave empty to not check it.",
                            FieldKind.CHOICE,
                            options=MOVE_RESULT_OPTIONS,
                        ),
                        text_list_field(
                            "rules",
                            "Rules",
                            "The IDs of the rules below the Judge checks this "
                            "Move Outcome's situation, feeling and why against.",
                            "Rule ID",
                        ),
                    ],
                ),
                group_list_field(
                    "rules",
                    "Rules",
                    "What the Judge checks kept Move Outcomes against, e.g. says "
                    "the User wanted options, not questions. Each rule has an ID "
                    "and the check, written for the Judge; the case fails if any "
                    "rule fails.",
                    "Rule",
                    RULES_FIELD.fields,
                    unique_by="id",
                ),
            ],
        ),
    ]
)

CASE_SHAPES: dict[EvalName, FormShape] = {
    EvalName.SAFEGUARD: SAFEGUARD_SHAPE,
    EvalName.PERSONA: PERSONA_SHAPE,
    EvalName.KNOWLEDGE: KNOWLEDGE_SHAPE,
    EvalName.SETTINGS: SETTINGS_SHAPE,
    EvalName.PHOTO_DESCRIPTIONS: PHOTO_DESCRIPTIONS_SHAPE,
    EvalName.UNDERSTANDING: UNDERSTANDING_SHAPE,
    EvalName.MOVE_OUTCOME: MOVE_OUTCOME_SHAPE,
}
