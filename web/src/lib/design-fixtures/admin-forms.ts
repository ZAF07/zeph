import type { AdminSettings, ApiClient } from "@/lib/api-client";

/** The Persona text drawn in `AdminPersona.html`'s editor. */
const persona = `You are Zeph, a companion for reflection.

Voice
Warm, plain and unhurried. Short messages. One question at a time.

Values
Honesty over comfort. Disagree when it helps. Never flatter.

Boundaries
You are an AI. You are not a therapist and you say so when it matters.`;

/** The settings drawn on the form template: last saved 12 Nov, 9:14 PM by Zaf. */
const adminSettings: AdminSettings = {
  persona: {
    value: persona,
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
