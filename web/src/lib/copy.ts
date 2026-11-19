import type { Metadata } from "next";

/** The website's Copy: every slot's current text, by slot key (ADR-0019). */
export type Copy = Record<string, string>;

/** Raised when the Copy has no slot with a key the page asks for. */
export class MissingCopyError extends Error {
  /**
   * @param key - The slot key the page asked for.
   */
  constructor(key: string) {
    super(`No Copy for ${key}`);
    this.name = "MissingCopyError";
  }
}

/**
 * Reads one slot's text. The web app holds no default text, so a missing
 * slot is an error rather than a blank.
 *
 * @param copy - The Copy.
 * @param key - The slot's key, e.g. `landing.hero.eyebrow`.
 * @returns The slot's text.
 * @throws MissingCopyError if there is no such slot.
 */
export function readCopy(copy: Copy, key: string): string {
  const text = copy[key];
  if (text === undefined) {
    throw new MissingCopyError(key);
  }
  return text;
}

/**
 * Fills a Copy text's `{name}` placeholders with live values. The text is
 * plain: nothing in it is read as markdown, links or HTML.
 *
 * @param text - The slot's text.
 * @param values - The value for each placeholder, by name.
 * @returns The text with each known placeholder replaced; a placeholder
 *   with no value is left as written.
 */
export function fillPlaceholders(
  text: string,
  values: Record<string, string | number>,
): string {
  return text.replace(/\{([^{}]*)\}/g, (placeholder, name: string) =>
    Object.hasOwn(values, name) ? String(values[name]) : placeholder,
  );
}

/**
 * Gives a website page's browser tab title and search description from
 * its tab's `page_title` and `page_description` slots.
 *
 * @param copy - The Copy.
 * @param tab - The page's Copy tab key, e.g. `pricing`.
 * @returns The page's title and description.
 * @throws MissingCopyError if the tab has no such slots.
 */
export function pageMetadata(copy: Copy, tab: string): Metadata {
  return {
    title: readCopy(copy, `${tab}.page_title`),
    description: readCopy(copy, `${tab}.page_description`),
  };
}
