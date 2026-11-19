import type { Copy } from "@/lib/copy";
import { seedTexts } from "@/lib/design-fixtures/copy";

/**
 * The seed Copy, as a fresh install serves it.
 *
 * @returns Every slot's seed text, by key.
 */
export function seedCopy(): Copy {
  return { ...seedTexts };
}

/**
 * Copy where every slot's text is its own key in marks, like
 * `⟦landing.faq.heading⟧`, so a test can tell Copy text from text written
 * into the page.
 *
 * @returns Every slot's marked key, by key.
 */
export function markedCopy(): Copy {
  return Object.fromEntries(
    Object.keys(seedTexts).map((key) => [key, `⟦${key}⟧`]),
  );
}

/**
 * Takes every marked Copy text out of some page text.
 *
 * @param text - Text from the page.
 * @returns What is left: text that did not come from Copy.
 */
export function withoutMarkedCopy(text: string): string {
  return text.replace(/⟦[^⟧]*⟧/g, "").trim();
}
