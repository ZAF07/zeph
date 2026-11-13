import { describe, expect, it } from "vitest";

import type { RecentCheckIn } from "@/lib/api-client";
import {
  checkInFrequencyText,
  greeting,
  lastCheckInText,
  lastConversationText,
  quietHoursText,
  todayHeading,
} from "@/lib/home";

const singapore = "Asia/Singapore";

function checkInWith(overrides: Partial<RecentCheckIn> = {}): RecentCheckIn {
  return {
    id: "c1",
    outcome: "sent",
    kind: "A casual hello",
    decided_at: "2026-11-09T10:00:00Z",
    status: "replied",
    skipped_for_daily_limit: false,
    ...overrides,
  };
}

describe("home wording", () => {
  it("greets the User for the time of day where they are", () => {
    expect(greeting("Maya", new Date("2026-11-11T01:00:00Z"), singapore)).toBe(
      "Good morning, Maya.",
    );
    expect(greeting("Maya", new Date("2026-11-11T06:00:00Z"), singapore)).toBe(
      "Good afternoon, Maya.",
    );
    expect(greeting("Maya", new Date("2026-11-11T12:00:00Z"), singapore)).toBe(
      "Good evening, Maya.",
    );
    expect(greeting(null, new Date("2026-11-11T12:00:00Z"), singapore)).toBe(
      "Good evening.",
    );
  });

  it("writes today's date where the User is", () => {
    expect(todayHeading(new Date("2026-11-11T12:00:00Z"), singapore)).toBe(
      "Wednesday, 11 November",
    );
  });

  it("says when the last Conversation was", () => {
    const now = new Date("2026-11-11T12:00:00Z");

    expect(lastConversationText("2026-11-11T11:48:00Z", now, singapore)).toBe(
      "Last Conversation today at 7:48 pm.",
    );
    expect(lastConversationText("2026-11-10T11:48:00Z", now, singapore)).toBe(
      "Last Conversation yesterday at 7:48 pm.",
    );
    expect(lastConversationText("2026-11-02T01:05:00Z", now, singapore)).toBe(
      "Last Conversation on 2 Nov at 9:05 am.",
    );
    expect(lastConversationText(null, now, singapore)).toBe(
      "No Conversations yet. Say hello in Telegram.",
    );
  });

  it("says how often Check-ins come, at most", () => {
    expect(checkInFrequencyText("few_times_a_week")).toBe(
      "A few times a week, at most",
    );
  });

  it("writes quiet hours as times of day", () => {
    expect(quietHoursText("22:00:00", "07:30:00")).toBe(
      "Never between 10:00 pm and 7:30 am",
    );
  });

  it("describes the last Check-in sent and whether the User replied", () => {
    expect(lastCheckInText(checkInWith(), singapore)).toBe(
      "Last Check-in: a casual hello, Mon 9 Nov · you replied",
    );
    expect(
      lastCheckInText(checkInWith({ status: "no_reply" }), singapore),
    ).toBe("Last Check-in: a casual hello, Mon 9 Nov · no reply");
    expect(
      lastCheckInText(
        checkInWith({
          outcome: "asked_about_fewer",
          kind: null,
          status: "sent",
        }),
        singapore,
      ),
    ).toBe("Last Check-in: asked if you’d like fewer, Mon 9 Nov");
    expect(lastCheckInText(null, singapore)).toBe("No Check-ins sent yet.");
  });
});
