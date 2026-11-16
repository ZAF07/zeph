import { describe, expect, it } from "vitest";

import {
  dueTimeText,
  heldBackText,
  quietHoursText,
  schedulePauseText,
} from "@/lib/check-in-schedule";

const now = "2026-11-17T02:00:00Z";
const singapore = "Asia/Singapore";

describe("Check-in Schedule wording", () => {
  it("says how long until the Due Time and when that is for the User", () => {
    expect(dueTimeText("2026-11-17T05:00:00Z", now, singapore)).toBe(
      "in 3 h · Tue 13:00 their time",
    );
  });

  it("counts minutes under an hour and days over two", () => {
    expect(dueTimeText("2026-11-17T02:40:00Z", now, singapore)).toBe(
      "in 40 min · Tue 10:40 their time",
    );
    expect(dueTimeText("2026-11-20T02:00:00Z", now, singapore)).toBe(
      "in 3 d · Fri 10:00 their time",
    );
  });

  it("says due now once the Due Time has come", () => {
    expect(dueTimeText(now, now, singapore)).toBe("due now");
    expect(dueTimeText("2026-11-16T02:00:00Z", now, singapore)).toBe("due now");
  });

  it("says when there is no Due Time", () => {
    expect(dueTimeText(null, now, singapore)).toBe("No Due Time");
  });

  it("names why a Check-in is held back and until when in the User's time", () => {
    expect(
      heldBackText(
        { reason: "quiet_hours", until: "2026-11-16T23:30:00Z" },
        now,
        singapore,
      ),
    ).toBe("Quiet Hours, until 07:30");
    expect(
      heldBackText(
        { reason: "paused", until: "2026-11-24T02:00:00Z" },
        now,
        singapore,
      ),
    ).toBe("Paused, until Tue 24 Nov 10:00");
    expect(
      heldBackText(
        { reason: "no_telegram_connection", until: null },
        now,
        singapore,
      ),
    ).toBe("No Telegram Connection");
    expect(
      heldBackText({ reason: "limit_skip_done_today", until: null }, now),
    ).toBe("Today’s message limit used up");
    expect(heldBackText({ reason: "no_kind_to_send", until: null }, now)).toBe(
      "No Kind to send",
    );
  });

  it("writes Quiet Hours as a range", () => {
    expect(quietHoursText("22:00:00", "07:30:00")).toBe("22:00–07:30");
  });

  it("writes the pause and until when", () => {
    expect(schedulePauseText(false, null, singapore)).toBe("Not paused");
    expect(schedulePauseText(true, null, singapore)).toBe(
      "Paused until resumed",
    );
    expect(schedulePauseText(true, "2026-11-24T02:00:00Z", singapore)).toBe(
      "Paused until Tue 24 Nov 10:00",
    );
  });
});
