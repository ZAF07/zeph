import type { Me, UserRole } from "@/lib/api-client";

/**
 * Builds a signed-in, onboarded User for tests.
 *
 * @param role - Whether they are a plain User or an Admin.
 * @returns The User.
 */
export function userWithRole(role: UserRole): Me {
  return {
    id: "user-1",
    email: "maya@example.com",
    name: "Maya",
    onboarding_reasons: [],
    onboarding_note: null,
    country: "SG",
    time_zone: "Asia/Singapore",
    ai_notice_acknowledged_at: "2026-11-11T09:00:00Z",
    user_memory_enabled: true,
    onboarding_completed_at: "2026-11-11T09:00:00Z",
    role,
  };
}
