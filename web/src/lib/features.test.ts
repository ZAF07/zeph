import { describe, expect, it } from "vitest";

import type { UserFeatureStatus } from "@/lib/api-client";
import {
  isOnForUser,
  lastChangeNote,
  switchForUser,
  userFeatureLine,
} from "@/lib/features";

const webSearch: UserFeatureStatus = {
  feature: "web_search",
  name: "Web search",
  works: true,
  reason: "on_for_everyone",
  switch: "default",
  changed_by_email: null,
  changed_at: null,
};

describe("lastChangeNote", () => {
  it("says a switch was never changed", () => {
    expect(lastChangeNote({ changed_at: null, changed_by_email: null })).toBe(
      "Never changed",
    );
  });

  it("names who changed it and when", () => {
    expect(
      lastChangeNote({
        changed_at: "2026-11-13T09:00:00Z",
        changed_by_email: "maya@example.com",
      }),
    ).toMatch(/^Changed 13 Nov, .+ by maya@example\.com$/);
  });
});

describe("userFeatureLine", () => {
  it("says a Feature works because it is on for everyone", () => {
    expect(userFeatureLine(webSearch, 0)).toBe("Works: on for everyone");
  });

  it("says a Feature is off for everyone", () => {
    expect(
      userFeatureLine(
        { ...webSearch, works: false, reason: "off_for_everyone" },
        0,
      ),
    ).toBe("Off for everyone");
  });

  it("explains a Feature turned on or off for one User", () => {
    expect(
      userFeatureLine({ ...webSearch, reason: "on_for_user", switch: "on" }, 0),
    ).toBe("Works: on for this user");
    expect(
      userFeatureLine(
        { ...webSearch, works: false, reason: "off_for_user", switch: "off" },
        0,
      ),
    ).toBe("Off for this user");
  });

  it("counts the Personal Stickers kept on the Stickers line only", () => {
    const stickers = { ...webSearch, feature: "stickers" as const };
    expect(userFeatureLine(stickers, 4)).toBe(
      "Works · 4 personal stickers kept",
    );
    expect(
      userFeatureLine(
        { ...stickers, works: false, reason: "off_for_everyone" },
        1,
      ),
    ).toBe("Off for everyone · 1 personal sticker kept");
    expect(userFeatureLine(webSearch, 4)).toBe("Works: on for everyone");
  });
});

describe("isOnForUser", () => {
  it("follows everyone's switch on Default", () => {
    expect(isOnForUser("default", true)).toBe(true);
    expect(isOnForUser("default", false)).toBe(false);
  });

  it("follows the User's own switch otherwise", () => {
    expect(isOnForUser("on", false)).toBe(true);
    expect(isOnForUser("off", true)).toBe(false);
  });
});

describe("switchForUser", () => {
  it("goes back to Default when it matches everyone's switch", () => {
    expect(switchForUser(true, true)).toBe("default");
    expect(switchForUser(false, false)).toBe("default");
  });

  it("sets On or Off for the User when it differs", () => {
    expect(switchForUser(true, false)).toBe("on");
    expect(switchForUser(false, true)).toBe("off");
  });
});
