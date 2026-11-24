import type { ApiClient, PatternType } from "@/lib/api-client";
import seedPatternCatalog from "@/lib/design-fixtures/seed-pattern-catalog.json";

/**
 * The Pattern Catalog as the backend serves it from its YAML files
 * (`src/companion/seed/pattern_catalog/`), copied as JSON. A backend test
 * keeps the two the same, so the pixel test checks the real Pattern Types
 * against the design reference.
 */
const patternTypes = seedPatternCatalog.pattern_types as PatternType[];

/** The Pattern Catalog page's calls, answered with the seed Pattern Types. */
export const patternCatalogFixtures: Partial<ApiClient> = {
  getPatternCatalog: async () => patternTypes,
};
