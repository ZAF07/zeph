from companion.core.knowledge import split_into_chunks


def test_short_paragraphs_share_a_chunk_and_pdf_line_breaks_become_spaces() -> None:
    text = "# Breath\n\nNotice the\nbreath.\n\n\n  Return gently.  "

    assert split_into_chunks(text) == [
        "# Breath\n\nNotice the breath.\n\nReturn gently."
    ]


def test_chunks_never_pass_the_limit_and_keep_every_word_in_order() -> None:
    sentences = [f"Sentence number {n} is here." for n in range(40)]
    text = "Short opening.\n\n" + " ".join(sentences)

    chunks = split_into_chunks(text, max_characters=40)

    assert all(len(chunk) <= 40 for chunk in chunks)
    assert " ".join(chunks).split() == text.split()
    assert chunks[:2] == ["Short opening.", "Sentence number 0 is here."]


def test_a_word_longer_than_the_limit_is_cut() -> None:
    assert split_into_chunks("x" * 45, max_characters=40) == ["x" * 40, "x" * 5]


def test_blank_text_has_no_chunks() -> None:
    assert split_into_chunks(" \n\n \t ") == []
