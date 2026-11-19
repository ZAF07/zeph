import { describe, expect, it } from "vitest";

import {
  fillPlaceholderParts,
  fillPlaceholders,
  MissingCopyError,
  pageMetadata,
  pickCopy,
  readCopy,
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
