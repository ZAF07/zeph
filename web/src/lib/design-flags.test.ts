import { describe, expect, it } from "vitest";

import { hasDesignFlag } from "@/lib/design-flags";

describe("hasDesignFlag", () => {
  it("reads ?design= on design fixtures", () => {
    const search = new URLSearchParams("design=menu-folded");

    expect(hasDesignFlag(search, "menu-folded", true)).toBe(true);
    expect(hasDesignFlag(search, "menu-open", true)).toBe(false);
  });

  it("ignores ?design= when fixture mode is off", () => {
    const search = new URLSearchParams("design=menu-folded");

    expect(hasDesignFlag(search, "menu-folded", false)).toBe(false);
  });
});
