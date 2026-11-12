import { describe, expect, it } from "vitest";

import { compareTexts } from "@/lib/text-changes";

describe("compareTexts", () => {
  it("marks added and removed words and counts them", () => {
    const comparison = compareTexts(
      "Notice the breath gently.",
      "Notice the slow breath.",
    );

    const side = (kind: "added" | "removed") =>
      comparison.parts
        .map((part) =>
          part.kind === "same" || part.kind === kind ? part.text : "",
        )
        .join("");
    expect(side("removed")).toBe("Notice the breath gently.");
    expect(side("added")).toBe("Notice the slow breath.");
    expect(comparison.parts[0]).toEqual({ kind: "same", text: "Notice the " });
  });

  it("counts the words added and removed", () => {
    expect(
      compareTexts("Notice the breath.", "Notice the slow, warm breath."),
    ).toMatchObject({ addedWords: 2, removedWords: 0, hasChanges: true });
    expect(
      compareTexts("Notice the slow breath.", "Notice the breath."),
    ).toMatchObject({ addedWords: 0, removedWords: 1 });
  });

  it("shortens long unchanged stretches, keeping a little either side", () => {
    const filler = "word ".repeat(200);
    const comparison = compareTexts(`${filler}old end`, `${filler}new end`);

    const [first] = comparison.parts;
    expect(first.kind).toBe("skipped");
    expect(comparison.parts[1]).toEqual({
      kind: "same",
      text: filler.slice(-80),
    });
  });

  it("says when nothing changed", () => {
    expect(compareTexts("Same text.", "Same text.").hasChanges).toBe(false);
  });
});
