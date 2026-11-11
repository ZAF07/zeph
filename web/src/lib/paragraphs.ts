/**
 * Splits text into paragraphs at blank lines.
 *
 * @param text - The text.
 * @returns The paragraphs, without empty ones.
 */
export function paragraphs(text: string): string[] {
  return text.split(/\n\s*\n/).filter((paragraph) => paragraph.trim());
}
