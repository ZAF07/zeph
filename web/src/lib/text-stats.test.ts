import { describe, expect, it } from "vitest";

import { countWords, describeLength } from "@/lib/text-stats";

describe("countWords", () => {
  it("counts words across spaces, lines and Markdown marks", () => {
    expect(countWords("# Breath\n\nNotice  the breath.\n")).toBe(5);
  });

  it("counts nothing in blank text", () => {
    expect(countWords("  \n ")).toBe(0);
  });
});

describe("describeLength", () => {
  it("writes the word and character count with thousands separators", () => {
    expect(describeLength("word ".repeat(1200).trim())).toBe(
      "1,200 words · 5,999 characters",
    );
  });

  it("uses the singular for one", () => {
    expect(describeLength("a")).toBe("1 word · 1 character");
  });
});
