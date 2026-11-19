import type { ApiClient } from "@/lib/api-client";

/**
 * Design fixtures for the Admin (Overview) reference
 * pages. Values come only from those reference files. Only the issue
 * building this area fills it.
 */
export const overviewFixtures: Partial<ApiClient> = {};

/** One count at the top of the Overview. */
export type OverviewCount = {
  label: string;
  value: string;
  caption: string;
  toBuild: boolean;
};

/** One thing in the Overview's "Needs attention" list, and where to fix it. */
export type AttentionItem = {
  text: string;
  linkLabel: string;
  href: string;
};

/** One Feature in the Overview's Features summary. */
export type FeatureSummary = { name: string; isOn: boolean };

/** One day's bar in the Overview's messages chart, as a share of its height. */
export type MessagesDay = { day: string; heightPercent: number };

/** One line of the Overview's Knowledge summary. */
export type KnowledgeLine = { label: string; value: string };

/**
 * What the Admin Overview shows. Its counts have no backend yet ("To
 * build"), so every mode shows these drawn values under a "Sample data"
 * label.
 */
export type OverviewSample = {
  counts: OverviewCount[];
  needsAttention: AttentionItem[];
  features: FeatureSummary[];
  messagesByDay: MessagesDay[];
  knowledge: KnowledgeLine[];
};

/** The Overview's values, as `Admin.html` draws them. */
export const overviewSample: OverviewSample = {
  counts: [
    {
      label: "Users",
      value: "128",
      caption: "96 connected to Telegram",
      toBuild: false,
    },
    {
      label: "Messages today",
      value: "1,840",
      caption: "limit 60 per user per day",
      toBuild: false,
    },
    {
      label: "Check-ins today",
      value: "212",
      caption: "41 more skipped to give space",
      toBuild: false,
    },
    {
      label: "Safeguard events",
      value: "2",
      caption: "in the last 7 days",
      toBuild: false,
    },
    {
      label: "Paying subscribers",
      value: "[N]",
      caption: "[BREAKDOWN BY PLAN]",
      toBuild: true,
    },
  ],
  needsAttention: [
    {
      text: "3 users reached the daily message limit today",
      linkLabel: "Open Usage",
      href: "/admin/usage",
    },
    {
      text: "1 knowledge document failed to process",
      linkLabel: "Open Knowledge",
      href: "/admin/knowledge",
    },
    {
      text: "Check-ins are not working for 2 opted-in users",
      linkLabel: "Open Check-in Schedule",
      href: "/admin/check-in-schedule",
    },
    {
      text: "2 safeguard events in the last 7 days",
      linkLabel: "Open Safeguard Events",
      href: "/admin/safeguard-events",
    },
  ],
  features: [
    { name: "Web search", isOn: true },
    { name: "Stickers", isOn: true },
    { name: "Knowledge", isOn: false },
  ],
  messagesByDay: [
    { day: "Wed", heightPercent: 62 },
    { day: "Thu", heightPercent: 70 },
    { day: "Fri", heightPercent: 58 },
    { day: "Sat", heightPercent: 44 },
    { day: "Sun", heightPercent: 48 },
    { day: "Mon", heightPercent: 81 },
    { day: "Tue", heightPercent: 76 },
  ],
  knowledge: [
    { label: "Ready", value: "5 documents" },
    { label: "Processing", value: "1 document" },
    { label: "Failed", value: "1 document" },
  ],
};
