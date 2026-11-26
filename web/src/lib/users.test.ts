import { describe, expect, it } from "vitest";

import {
  displayNameOf,
  noPatterns,
  otherPatternCounts,
  roleLabel,
} from "@/lib/users";

describe("displayNameOf", () => {
  it("uses the name, else the email, else This User", () => {
    expect(displayNameOf({ name: "Ren", email: "ren@example.com" })).toBe(
      "Ren",
    );
    expect(displayNameOf({ name: null, email: "ren@example.com" })).toBe(
      "ren@example.com",
    );
    expect(displayNameOf({ name: null, email: null })).toBe("This User");
  });
});

describe("roleLabel", () => {
  it("says Admin or User", () => {
    expect(roleLabel("admin")).toBe("Admin");
    expect(roleLabel("user")).toBe("User");
  });
});

describe("otherPatternCounts", () => {
  it("lists the states other than confirmed that have any, in order", () => {
    expect(
      otherPatternCounts({
        ...noPatterns,
        closed: 1,
        unmatched: 4,
        noticed: 4,
        confirmed: 2,
      }),
    ).toEqual([
      { label: "Noticed Patterns", value: "4" },
      { label: "Closed Patterns", value: "1" },
      { label: "Unmatched Patterns", value: "4" },
    ]);
  });

  it("lists nothing for a User with no Patterns", () => {
    expect(otherPatternCounts(noPatterns)).toEqual([]);
  });
});
