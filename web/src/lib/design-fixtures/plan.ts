import type { ApiClient } from "@/lib/api-client";

/**
 * Design fixtures for the Plan reference pages. Values come only from
 * those reference files. Only the issue building this area fills it.
 */
export const planFixtures: Partial<ApiClient> = {};

/** One plan a User can switch to on the Plan page. */
export type PlanChoice = {
  name: string;
  price: string;
  includes: string[];
  isCurrent: boolean;
};

/** One payment in the Plan page's billing history. */
export type BillingHistoryEntry = {
  date: string;
  plan: string;
  amount: string;
};

/**
 * What the Plan page shows. Plans have no backend yet ("To build"), so every
 * mode shows these drawn values, placeholders included.
 */
export type PlanSample = {
  name: string;
  price: string;
  renewalDate: string;
  messagesToday: string;
  dailyLimit: string;
  messagesUsedPercent: number;
  choices: PlanChoice[];
  paymentProvider: string;
  card: string;
  billingHistory: BillingHistoryEntry[];
};

const sampleIncludes = [
  "[WHAT THIS PLAN INCLUDES]",
  "[WHAT THIS PLAN INCLUDES]",
  "[WHAT THIS PLAN INCLUDES]",
];

const samplePayment: BillingHistoryEntry = {
  date: "[DATE]",
  plan: "[PLAN NAME]",
  amount: "[AMOUNT]",
};

/** The Plan page's values, as `Plan.html` draws them. */
export const planSample: PlanSample = {
  name: "[PLAN NAME]",
  price: "[PRICE]",
  renewalDate: "[RENEWAL DATE]",
  messagesToday: "[N]",
  dailyLimit: "[DAILY LIMIT]",
  messagesUsedPercent: 38,
  choices: [
    {
      name: "[PLAN NAME]",
      price: "[PRICE]",
      includes: sampleIncludes,
      isCurrent: false,
    },
    {
      name: "[PLAN NAME]",
      price: "[PRICE]",
      includes: sampleIncludes,
      isCurrent: true,
    },
    {
      name: "[PLAN NAME]",
      price: "[PRICE]",
      includes: sampleIncludes,
      isCurrent: false,
    },
  ],
  paymentProvider: "[PAYMENT PROVIDER]",
  card: "[CARD BRAND] ending [LAST 4]",
  billingHistory: [samplePayment, samplePayment, samplePayment],
};
