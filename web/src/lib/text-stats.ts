/**
 * Counts the words in a text: runs of characters between spaces.
 *
 * @param text - The text.
 * @returns How many words it has; 0 if it is blank.
 */
export function countWords(text: string): number {
  return text.split(/\s+/).filter((word) => word !== "").length;
}

/**
 * Writes a text's length, like "1,204 words · 6,880 characters".
 *
 * @param text - The text.
 * @returns Its word and character count.
 */
export function describeLength(text: string): string {
  const words = countWords(text);
  const characters = text.length;
  return `${words.toLocaleString("en-GB")} ${words === 1 ? "word" : "words"} · ${characters.toLocaleString("en-GB")} ${characters === 1 ? "character" : "characters"}`;
}
