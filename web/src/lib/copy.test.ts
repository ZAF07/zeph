import { describe, expect, it } from "vitest";

import {
  fillCopy,
  fillPlaceholderParts,
  fillPlaceholders,
  MissingCopyError,
  pageMetadata,
  pickCopy,
  readCopy,
  readCountCopy,
} from "@/lib/copy";

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

describe("pageMetadata", () => {
  it("gives a page's tab title and description from its tab's slots", () => {
    const copy = {
      "pricing.page_title": "Zeph — Pricing",
      "pricing.page_description": "Simple plans.",
    };

    expect(pageMetadata(copy, "pricing")).toEqual({
      title: "Zeph — Pricing",
      description: "Simple plans.",
    });
  });

  it("fails rather than leave the title blank when a slot is missing", () => {
    expect(() => pageMetadata({}, "pricing")).toThrow(MissingCopyError);
  });
});

describe("fillPlaceholderParts", () => {
  it("puts each part in place of its placeholder, keeping the text around it", () => {
    const terms = { kind: "terms link" };
    const privacy = { kind: "privacy link" };

    expect(
      fillPlaceholderParts("Agree to the {terms} and {privacy}.", {
        terms,
        privacy,
      }),
    ).toEqual(["Agree to the ", terms, " and ", privacy, "."]);
  });

  it("follows the placeholders wherever an Admin moved them", () => {
    const terms = { kind: "terms link" };
    const privacy = { kind: "privacy link" };

    expect(
      fillPlaceholderParts("{privacy}, then {terms}", { terms, privacy }),
    ).toEqual([privacy, ", then ", terms]);
  });

  it("leaves a placeholder it has no part for as written", () => {
    expect(fillPlaceholderParts("See {nmae}", {})).toEqual(["See ", "{nmae}"]);
  });
});

describe("fillCopy", () => {
  it("reads a slot and fills its placeholders", () => {
    const copy = { "home.goals.remembered": "Remembered {day}" };

    expect(fillCopy(copy, "home.goals.remembered", { day: "2 Oct" })).toBe(
      "Remembered 2 Oct",
    );
  });

  it("raises for a slot the Copy doesn't have", () => {
    expect(() => fillCopy({}, "home.goals.remembered", {})).toThrow(
      MissingCopyError,
    );
  });
});

describe("pickCopy", () => {
  it("keeps only the slots whose keys start with one of the prefixes", () => {
    const copy = {
      "onboarding.hello.heading": "Hello.",
      "onboarding.hello.intro": "I’m Zeph.",
      "shared.wordmark": "Zeph",
      "shared.footer.line": "On Telegram.",
      "landing.hero.eyebrow": "Your AI companion",
    };

    expect(pickCopy(copy, ["onboarding.", "shared.wordmark"])).toEqual({
      "onboarding.hello.heading": "Hello.",
      "onboarding.hello.intro": "I’m Zeph.",
      "shared.wordmark": "Zeph",
    });
  });
});

describe("readCountCopy", () => {
  const copy = {
    "memories.confirm_body_one": "Forget the {count} memory.",
    "memories.confirm_body_many": "Forget all {count} memories.",
  };

  it("picks the one slot for 1, with the count filled in", () => {
    expect(readCountCopy(copy, "memories.confirm_body", 1)).toBe(
      "Forget the 1 memory.",
    );
  });

  it.each([0, 2, 37])("picks the many slot for %i", (count) => {
    expect(readCountCopy(copy, "memories.confirm_body", count)).toBe(
      `Forget all ${count} memories.`,
    );
  });

  it("fails naming the slot when the Copy has no such slot", () => {
    expect(() => readCountCopy({}, "memories.confirm_body", 1)).toThrow(
      new MissingCopyError("memories.confirm_body_one"),
    );
  });
});
