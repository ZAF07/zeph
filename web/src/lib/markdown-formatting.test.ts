import { describe, expect, it } from "vitest";

import {
  formatMarkdown,
  type MarkdownFormat,
  type TextEdit,
} from "@/lib/markdown-formatting";

/**
 * Applies a formatting edit and marks the new selection with [ and ].
 */
function apply(marked: string, format: MarkdownFormat): string {
  const from = marked.indexOf("[");
  const to = marked.indexOf("]") - 1;
  const text = marked.replace("[", "").replace("]", "");
  const edit: TextEdit = formatMarkdown(text, from, to, format);
  const result = text.slice(0, edit.from) + edit.insert + text.slice(edit.to);
  return (
    result.slice(0, edit.selectionFrom) +
    "[" +
    result.slice(edit.selectionFrom, edit.selectionTo) +
    "]" +
    result.slice(edit.selectionTo)
  );
}

describe("formatMarkdown, inline", () => {
  it("wraps the selection in bold or italic marks", () => {
    expect(apply("Notice the [breath] now", "bold")).toBe(
      "Notice the **[breath]** now",
    );
    expect(apply("Notice the [breath] now", "italic")).toBe(
      "Notice the _[breath]_ now",
    );
  });

  it("puts the cursor between the marks when nothing is selected", () => {
    expect(apply("Notice []", "bold")).toBe("Notice **[]**");
  });

  it("removes the marks when the selection is already wrapped", () => {
    expect(apply("Notice the **[breath]** now", "bold")).toBe(
      "Notice the [breath] now",
    );
  });
});

describe("formatMarkdown, lines", () => {
  it("turns the current line into a heading, keeping the cursor in place", () => {
    expect(apply("Mindful br[]eathing\n\nText", "heading")).toBe(
      "## Mindful br[]eathing\n\nText",
    );
  });

  it("removes the heading when the line is already one", () => {
    expect(apply("## Mindful[] breathing", "heading")).toBe(
      "Mindful[] breathing",
    );
  });

  it("quotes or lists every selected line, skipping blank lines", () => {
    expect(apply("[one\n\ntwo]", "quote")).toBe("[> one\n\n> two]");
    expect(apply("[one\ntwo]", "bulletList")).toBe("[- one\n- two]");
    expect(apply("Intro\n[one\ntwo\nthree]", "numberedList")).toBe(
      "Intro\n[1. one\n2. two\n3. three]",
    );
  });

  it("removes the list marks when every line already has them", () => {
    expect(apply("[- one\n- two]", "bulletList")).toBe("[one\ntwo]");
    expect(apply("[1. one\n2. two]", "numberedList")).toBe("[one\ntwo]");
  });

  it("numbers a part-numbered selection afresh, without doubling marks", () => {
    expect(apply("[3. one\ntwo]", "numberedList")).toBe("[1. one\n2. two]");
    expect(apply("[### one\ntwo]", "heading")).toBe("[## one\n## two]");
  });

  it("starts a list on an empty line", () => {
    expect(apply("Intro\n[]", "bulletList")).toBe("Intro\n- []");
  });
});
