import { notFound } from "next/navigation";

import { StatesSheet } from "@/components/StatesSheet";
import { env } from "@/env";

/**
 * A preview of the design's `States` sheet, so the shared state parts can be
 * screenshotted next to `design/baseline/States.png`. Found only in
 * design-fixture mode (ADR 0018); everywhere else it is a 404.
 *
 * @returns The sheet.
 */
export default function StatesPreviewPage() {
  if (!env.designFixtures) {
    notFound();
  }
  return <StatesSheet />;
}
