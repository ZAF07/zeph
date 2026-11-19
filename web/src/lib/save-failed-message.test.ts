import { describe, expect, it } from "vitest";

import { ApiError } from "@/lib/api-client";
import {
  SAVE_FAILED_MESSAGE,
  saveFailedMessage,
} from "@/lib/save-failed-message";

describe("saveFailedMessage", () => {
  it("says nothing when the save hasn't failed", () => {
    expect(saveFailedMessage(null)).toBeNull();
  });

  it("gives the backend's reason when it refused the values", () => {
    const refused = new ApiError(422, "/admin/settings", "Keep {helplines}.");

    expect(saveFailedMessage(refused)).toBe("Keep {helplines}.");
  });

  it("gives the page's own words for any other failure", () => {
    expect(saveFailedMessage(new Error("down"), "Couldn’t save.")).toBe(
      "Couldn’t save.",
    );
  });

  it("gives the design's words by default", () => {
    expect(saveFailedMessage(new Error("down"))).toBe(SAVE_FAILED_MESSAGE);
    expect(saveFailedMessage(new ApiError(500, "/admin/settings"))).toBe(
      "Couldn’t save. Your text is still here.",
    );
  });
});
