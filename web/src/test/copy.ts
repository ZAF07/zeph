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

/**
 * Says what words on a rendered page did not come from marked Copy: its
 * text, icons aside, and every label read out by screen readers. Bare
 * numbers, such as step numbers, are not words.
 *
 * @param container - The rendered page.
 * @returns Each piece of text not from Copy; empty when every word is Copy.
 */
export function wordsNotFromCopy(container: HTMLElement): string[] {
  const words = container.cloneNode(true) as HTMLElement;
  words
    .querySelectorAll("[aria-hidden='true']")
    .forEach((icon) => icon.remove());
  const labels = Array.from(words.querySelectorAll("[aria-label]")).map(
    (element) => element.getAttribute("aria-label") ?? "",
  );
  return [words.textContent ?? "", ...labels]
    .map((text) => withoutMarkedCopy(text).replace(/\d/g, "").trim())
    .filter((text) => text !== "");
}
