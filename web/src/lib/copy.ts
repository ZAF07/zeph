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

/**
 * Fills a Copy text's `{name}` placeholders with page parts, such as links,
 * so an Admin can move a link within the sentence but not drop it.
 *
 * @param text - The slot's text.
 * @param parts - The part for each placeholder, by name.
 * @returns The text split into its plain pieces and the parts, in order;
 *   a placeholder with no part is left as written.
 */
export function fillPlaceholderParts<Part>(
  text: string,
  parts: Record<string, Part>,
): (string | Part)[] {
  return text
    .split(/(\{[^{}]*\})/)
    .filter((piece) => piece !== "")
    .map((piece) => {
      const name = piece.slice(1, -1);
      const isPlaceholder = piece.startsWith("{") && piece.endsWith("}");
      return isPlaceholder && Object.hasOwn(parts, name) ? parts[name] : piece;
    });
}

/**
 * Picks the slots a client component needs, so the whole Copy isn't sent
 * to the browser.
 *
 * @param copy - The Copy.
 * @param prefixes - Key starts to keep, e.g. `onboarding.` or a whole key.
 * @returns Only the slots whose keys start with one of the prefixes.
 */
export function pickCopy(copy: Copy, prefixes: string[]): Copy {
  return Object.fromEntries(
    Object.entries(copy).filter(([key]) =>
      prefixes.some((prefix) => key.startsWith(prefix)),
    ),
  );
}
