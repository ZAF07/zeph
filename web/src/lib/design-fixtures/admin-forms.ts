import type { AdminSettings, ApiClient } from "@/lib/api-client";

/** The Persona text drawn in `AdminPersona.html`'s editor. */
const persona = `You are Zeph, a companion for reflection.

Voice
Warm, plain and unhurried. Short messages. One question at a time.

Values
Honesty over comfort. Disagree when it helps. Never flatter.

Boundaries
You are an AI. You are not a therapist and you say so when it matters.`;

/**
 * The settings drawn on the form template: last saved 12 Nov, 9:14 PM by
 * Zaf, with the Voice editor's hint. The Ignore Threshold is 3, as the
 * Check-in log's paused row says.
 */
const adminSettings: AdminSettings = {
  persona: {
    label: "Persona",
    hint: "How Zeph speaks: its tone, values and boundaries. The Reply reads this before every message, and so does a Check-in sent on its own.",
    value: persona,
    updated_at: "2026-11-12T21:14:00+08:00",
    updated_by: "Zaf",
  },
  check_in_ignore_threshold: {
    label: "Ignore threshold",
    hint: "",
    value: 3,
    updated_at: "2026-11-12T21:14:00+08:00",
    updated_by: "Zaf",
  },
};

/**
 * Design fixtures for the AdminPersona (the form template) reference
 * pages. Values come only from those reference files. Only the issue
 * building this area fills it.
 */
export const adminFormsFixtures: Partial<ApiClient> = {
  getAdminSettings: () => Promise.resolve(adminSettings),
};
