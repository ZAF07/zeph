import type { NextConfig } from "next";

import { checkServerSettings } from "@/env";

/**
 * Builds the Next.js config, checking server settings first.
 *
 * @param phase - The Next.js phase the config is loaded for.
 * @returns The Next.js config.
 */
export default function buildNextConfig(phase: string): NextConfig {
  checkServerSettings(phase);
  return {};
}
