import { describe, expect, it } from "vitest";

import { displayNameOf, roleLabel } from "@/lib/users";

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
