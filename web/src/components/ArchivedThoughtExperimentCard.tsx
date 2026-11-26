import { CardCount } from "@/components/CardCount";
import { CardSaveBar } from "@/components/CardSaveBar";
import { FoldingCard } from "@/components/FoldingCard";
import type { ThoughtExperiment } from "@/lib/api-client";
import { askedWords, pairTitle } from "@/lib/thought-experiment-draft";

/**
 * One archived Thought Experiment as a card of the card list, read only.
 * The folded row shows the two Pattern Types, the start of its wording and
 * how many times it was asked. Open, it shows the whole wording.
 *
 * @param props - `thoughtExperiment` is the archived one; `isOpen` and
 *   `onToggle` open and fold it.
 * @returns The card.
 */
export function ArchivedThoughtExperimentCard({
  thoughtExperiment,
  isOpen,
  onToggle,
}: {
  thoughtExperiment: ThoughtExperiment;
  isOpen: boolean;
  onToggle: () => void;
}) {
  return (
    <FoldingCard
      title={pairTitle(thoughtExperiment)}
      summary={thoughtExperiment.wording}
      meta={
        <CardCount
          count={thoughtExperiment.asked_count}
          words={askedWords(thoughtExperiment.asked_count)}
        />
      }
      isDirty={false}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <p className="m-0 text-[15px] text-text">{thoughtExperiment.wording}</p>
      <CardSaveBar note="Archived: Zeph never asks it again. Past tries still show it." />
    </FoldingCard>
  );
}
