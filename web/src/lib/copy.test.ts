import { describe, expect, it } from "vitest";

import { fillPlaceholders, MissingCopyError, readCopy } from "@/lib/copy";

describe("fillPlaceholders", () => {
  it("puts each value in place of its placeholder, wherever it sits", () => {
    expect(
      fillPlaceholders("{name}, you have {count} Memory Items", {
        name: "Alex",
        count: 3,
      }),
    ).toBe("Alex, you have 3 Memory Items");
    expect(fillPlaceholders("Memory Items: {count}", { count: 12 })).toBe(
      "Memory Items: 12",
    );
  });

  it("fills a placeholder used more than once every time", () => {
    expect(fillPlaceholders("{count} of {count}", { count: 2 })).toBe("2 of 2");
  });

  it("leaves text with no placeholders as it is", () => {
    expect(fillPlaceholders("Think Deeper,", {})).toBe("Think Deeper,");
  });

  it("leaves a placeholder it has no value for as written", () => {
    expect(fillPlaceholders("Hi {name}", {})).toBe("Hi {name}");
  });

  it("treats the text as plain, never as markup", () => {
    expect(
      fillPlaceholders("**Bold** <b>{name}</b>", { name: "<i>A</i>" }),
    ).toBe("**Bold** <b><i>A</i></b>");
  });
});

describe("readCopy", () => {
  it("reads a slot's text by key", () => {
    expect(
      readCopy(
        { "landing.faq.heading": "Common questions." },
        "landing.faq.heading",
      ),
    ).toBe("Common questions.");
  });

  it("fails naming the slot when the Copy has no such slot", () => {
    expect(() => readCopy({}, "landing.faq.heading")).toThrow(
      new MissingCopyError("landing.faq.heading"),
    );
  });
});
