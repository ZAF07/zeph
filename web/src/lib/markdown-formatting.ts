/** The Markdown formatting the text editor's toolbar offers. */
export type MarkdownFormat =
  "heading" | "bold" | "italic" | "quote" | "bulletList" | "numberedList";

/** One change to a text: replace `from`–`to` with `insert`, then select. */
export type TextEdit = {
  from: number;
  to: number;
  insert: string;
  selectionFrom: number;
  selectionTo: number;
};

type FormatRule =
  { kind: "inline"; mark: string } | { kind: "line"; pattern: RegExp };

const headingPattern = /^#{1,6} /;

const formatRules: Record<MarkdownFormat, FormatRule> = {
  heading: { kind: "line", pattern: headingPattern },
  bold: { kind: "inline", mark: "**" },
  italic: { kind: "inline", mark: "_" },
  quote: { kind: "line", pattern: /^> / },
  bulletList: { kind: "line", pattern: /^[-*] / },
  numberedList: { kind: "line", pattern: /^\d+\. / },
};

/**
 * Wraps the selection in a mark like "**", or unwraps it if it is wrapped.
 *
 * @param text - The whole text.
 * @param from - Where the selection starts.
 * @param to - Where the selection ends.
 * @param mark - The mark, like "**" for bold.
 * @returns The edit.
 */
function toggleInlineMark(
  text: string,
  from: number,
  to: number,
  mark: string,
): TextEdit {
  const selected = text.slice(from, to);
  const isWrapped =
    text.slice(from - mark.length, from) === mark &&
    text.slice(to, to + mark.length) === mark;
  if (isWrapped) {
    return {
      from: from - mark.length,
      to: to + mark.length,
      insert: selected,
      selectionFrom: from - mark.length,
      selectionTo: to - mark.length,
    };
  }
  return {
    from,
    to,
    insert: `${mark}${selected}${mark}`,
    selectionFrom: from + mark.length,
    selectionTo: to + mark.length,
  };
}

/**
 * Writes the prefix a line gets for a line format.
 *
 * @param format - The line format.
 * @param number - The line's place in a numbered list, from 1.
 * @returns The prefix, like "## " or "2. ".
 */
function prefixFor(format: MarkdownFormat, number: number): string {
  switch (format) {
    case "heading":
      return "## ";
    case "quote":
      return "> ";
    case "bulletList":
      return "- ";
    default:
      return `${number}. `;
  }
}

/**
 * Adds a line format to every selected line, or removes it if they all
 * have it. Blank lines are skipped unless every line is blank.
 *
 * @param text - The whole text.
 * @param from - Where the selection starts.
 * @param to - Where the selection ends.
 * @param format - The line format.
 * @param pattern - Matches the format's prefix at a line's start.
 * @returns The edit.
 */
function toggleLinePrefix(
  text: string,
  from: number,
  to: number,
  format: MarkdownFormat,
  pattern: RegExp,
): TextEdit {
  const lineStart = text.lastIndexOf("\n", from - 1) + 1;
  const nextBreak = text.indexOf("\n", to);
  const lineEnd = nextBreak === -1 ? text.length : nextBreak;
  const lines = text.slice(lineStart, lineEnd).split("\n");
  const allBlank = lines.every((line) => line.trim() === "");
  const shouldRemove =
    !allBlank &&
    lines
      .filter((line) => line.trim() !== "")
      .every((line) => pattern.test(line));
  let number = 0;
  const newLines = lines.map((line) => {
    if (shouldRemove) {
      return line.replace(pattern, "");
    }
    if (!allBlank && line.trim() === "") {
      return line;
    }
    number += 1;
    const unformatted =
      format === "heading" ? line.replace(headingPattern, "") : line;
    return prefixFor(format, number) + unformatted;
  });
  const insert = newLines.join("\n");
  if (lines.length === 1 && from === to) {
    const cursor = Math.max(
      lineStart,
      from + newLines[0].length - lines[0].length,
    );
    return {
      from: lineStart,
      to: lineEnd,
      insert,
      selectionFrom: cursor,
      selectionTo: cursor,
    };
  }
  return {
    from: lineStart,
    to: lineEnd,
    insert,
    selectionFrom: lineStart,
    selectionTo: lineStart + insert.length,
  };
}

/**
 * Works out the edit that applies a Markdown format to a selection, or
 * removes it when it is already there.
 *
 * @param text - The whole text.
 * @param from - Where the selection starts.
 * @param to - Where the selection ends.
 * @param format - The format to apply.
 * @returns The edit to make.
 */
export function formatMarkdown(
  text: string,
  from: number,
  to: number,
  format: MarkdownFormat,
): TextEdit {
  const rule = formatRules[format];
  if (rule.kind === "inline") {
    return toggleInlineMark(text, from, to, rule.mark);
  }
  return toggleLinePrefix(text, from, to, format, rule.pattern);
}
