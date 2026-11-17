import {
  PHASE_PRODUCTION_BUILD,
  PHASE_PRODUCTION_SERVER,
} from "next/constants";
import { afterEach, describe, expect, it, vi } from "vitest";

import { checkServerSettings } from "@/env";

describe("checkServerSettings", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("refuses to start the server when CLERK_SECRET_KEY is missing", () => {
    vi.stubEnv("CLERK_SECRET_KEY", "");

    expect(() => checkServerSettings(PHASE_PRODUCTION_SERVER)).toThrow(
      "Missing required setting in .env: CLERK_SECRET_KEY",
    );
  });

  it("starts the server when CLERK_SECRET_KEY is set", () => {
    vi.stubEnv("CLERK_SECRET_KEY", "sk_test_placeholder");

    expect(() => checkServerSettings(PHASE_PRODUCTION_SERVER)).not.toThrow();
  });

  it("builds without CLERK_SECRET_KEY so the secret is never baked into the image", () => {
    vi.stubEnv("CLERK_SECRET_KEY", "");

    expect(() => checkServerSettings(PHASE_PRODUCTION_BUILD)).not.toThrow();
  });
});
