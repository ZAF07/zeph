/**
 * A count with its words, the number brighter, as on a card list's
 * toolbar ("6 kinds") and folded rows ("58 sent in 30 days").
 *
 * @param props - `count` is the number; `words` follow it.
 * @returns The count.
 */
export function CardCount({ count, words }: { count: number; words: string }) {
  return (
    <>
      <span className="text-text">{count}</span> {words}
    </>
  );
}
