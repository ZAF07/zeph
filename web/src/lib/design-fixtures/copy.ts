import type { ApiClient, CopyTab } from "@/lib/api-client";
import type { Copy } from "@/lib/copy";
import seedCopy from "@/lib/design-fixtures/seed-copy.json";

/** One slot as the backend's Copy seed file defines it. */
type SeedSlot = {
  key: string;
  name: string;
  max_length: number;
  text: string;
  placeholders?: string[];
};

/** One tab as the backend's Copy seed file defines it. */
type SeedTab = { tab: string; name: string; slots: SeedSlot[] };

/**
 * The backend's Copy seed file (`src/companion/seed/copy.yaml`), copied as
 * JSON. A backend test keeps the two the same, so the pixel test checks the
 * seed text against the design references.
 */
const seedTabs: SeedTab[] = seedCopy;

/** Every slot's seed text, by key, as the public Copy read returns it. */
export const seedTexts: Copy = Object.fromEntries(
  seedTabs.flatMap((tab) => tab.slots.map((slot) => [slot.key, slot.text])),
);

/** The Copy page with every slot still on its seed text. */
const copyPage: CopyTab[] = seedTabs.map((tab) => ({
  tab: tab.tab,
  name: tab.name,
  slots: tab.slots.map((slot) => ({
    key: slot.key,
    name: slot.name,
    text: slot.text,
    max_length: slot.max_length,
    placeholders: slot.placeholders ?? [],
    updated_at: "2026-11-12T21:14:00+08:00",
    updated_by: null,
  })),
}));

/**
 * Design fixtures for Copy: the seed text, which matches the reference
 * files, for the public pages and the Copy admin page.
 */
export const copyFixtures: Partial<ApiClient> = {
  getCopy: () => Promise.resolve(seedTexts),
  getCopyPage: () => Promise.resolve(copyPage),
};
