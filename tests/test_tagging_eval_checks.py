import pytest

from companion.core.evals.tagging_eval import gendered_words


@pytest.mark.parametrize(
    ("context", "found"),
    [
        ("She agreed to help her mother.", ["she", "her"]),
        ("He told himself it was fine; it was his call.", ["he", "himself", "his"]),
        ("Mei asked him and he said yes, it's hers now", ["him", "he", "hers"]),
        ("They agreed to help their mother again.", []),
        ("Felt the heat; shed a tear; the herbs in the hearth.", []),
        ("", []),
    ],
)
def test_gendered_words_finds_each_he_or_she_word_once_as_a_whole_word(
    context: str, found: list[str]
) -> None:
    assert gendered_words(context) == found
