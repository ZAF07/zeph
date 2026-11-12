import { describe, expect, it } from "vitest";

import type { DailyUsage } from "@/lib/api-client";
import {
  formatUsageCount,
  limitsReached,
  summarizeUsage,
  usageCsv,
} from "@/lib/usage";

function row(overrides: Partial<DailyUsage>): DailyUsage {
  return {
    day: "2026-11-11",
    user_id: "user-1",
    user_name: "Maya Lin",
    user_email: "maya@example.com",
    message_count: 24,
    tokens_in: 31240,
    tokens_out: 3880,
    web_search_count: 1,
    ...overrides,
  };
}

const limits = { daily_message_limit: 60, web_search_daily_limit: 10 };

describe("Usage", () => {
  it("adds up tokens, messages and web searches", () => {
    expect(
      summarizeUsage([
        row({}),
        row({
          message_count: 6,
          tokens_in: 10,
          tokens_out: 20,
          web_search_count: 3,
        }),
      ]),
    ).toEqual({
      tokensIn: 31250,
      tokensOut: 3900,
      messages: 30,
      webSearches: 4,
    });
  });

  it("writes big counts short and small ones in full", () => {
    expect(formatUsageCount(1_840_000)).toBe("1.84M");
    expect(formatUsageCount(212_000)).toBe("212K");
    expect(formatUsageCount(1406)).toBe("1,406");
    expect(formatUsageCount(88)).toBe("88");
  });

  it("says which daily limits a row reached", () => {
    expect(limitsReached(row({}), limits)).toEqual([]);
    expect(limitsReached(row({ message_count: 60 }), limits)).toEqual([
      "Message limit reached",
    ]);
    expect(
      limitsReached(row({ message_count: 60, web_search_count: 10 }), limits),
    ).toEqual(["Message limit reached", "Search limit reached"]);
    expect(
      limitsReached(row({ web_search_count: 0 }), {
        ...limits,
        web_search_daily_limit: 0,
      }),
    ).toEqual([]);
  });

  it("writes the rows as CSV, quoting text that needs it", () => {
    expect(
      usageCsv([
        row({}),
        row({ day: "2026-11-10", user_name: 'Ren "R", O.', user_email: null }),
      ]),
    ).toBe(
      [
        "Date,User,Email,Messages,Tokens in,Tokens out,Web searches",
        "2026-11-11,Maya Lin,maya@example.com,24,31240,3880,1",
        '2026-11-10,"Ren ""R"", O.",,24,31240,3880,1',
      ].join("\n"),
    );
  });
});
