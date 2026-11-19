import { cardListRow, panelCard } from "@/components/card-styles";
import { EmptyState } from "@/components/EmptyState";
import type { CopySearchMatch } from "@/lib/copy-search";

/**
 * The slots a Copy search found, each naming its tab and slot above the
 * slot's text. Picking one takes the Admin to it. A search that found
 * nothing shows the empty state.
 *
 * @param props - `matches` are the slots found, in order, and `onPick` is
 *   called with the match the Admin picks.
 * @returns The results, or the empty state.
 */
export function CopySearchResults({
  matches,
  onPick,
}: {
  matches: CopySearchMatch[];
  onPick: (match: CopySearchMatch) => void;
}) {
  if (matches.length === 0) {
    return (
      <EmptyState
        title="No slots match"
        body="No tab has a slot with that text. Try a few words from the sentence."
      />
    );
  }
  return (
    <ul aria-label="Search results" className={`m-0 list-none ${panelCard}`}>
      {matches.map((match) => (
        <li key={match.slot.key} className={cardListRow}>
          <button
            type="button"
            onClick={() => onPick(match)}
            className="flex min-h-11 w-full cursor-pointer flex-col items-start gap-1 border-0 bg-transparent p-0 text-left font-[inherit]"
          >
            <span className="text-[14px] text-text">
              {match.tab.name} · {match.slot.name}
            </span>
            <span className="text-[13px] text-soft">{match.slot.text}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}
