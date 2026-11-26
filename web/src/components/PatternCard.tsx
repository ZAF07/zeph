import { MemoryCard } from "@/components/MemoryCard";
import type {
  Pattern,
  PatternCondition,
  PredictionOutcome,
  WhereItShows,
} from "@/lib/api-client";
import { type Copy, fillCopy, readCopy } from "@/lib/copy";
import { formatShortCalendarDay, formatShortDay } from "@/lib/dates";

const conditionsAboutPeople: PatternCondition[] = ["relationship", "power"];
const blockLabel =
  "pb-2 text-[11px] font-medium tracking-[2px] text-soft uppercase";
const row = "flex flex-wrap gap-x-4 gap-y-0.5 border-t border-line py-2.5";
const rowName = "flex-[0_0_190px] text-[13px] text-soft";
const rowLines =
  "flex min-w-0 flex-[1_1_260px] flex-col gap-1.5 text-[14px] text-text";

/**
 * Names the Copy slot that says how a Prediction went.
 *
 * @param outcome - How it went; null while Zeph hasn't asked.
 * @returns The slot's key.
 */
function outcomeSlot(outcome: PredictionOutcome | null): string {
  return `memories.patterns.outcome.${outcome ?? "waiting"}`;
}

/**
 * Names the Copy slot that words one value of a Condition. A stored value
 * such as "one-to-one" or "worn out" is spelt with underscores in the key.
 *
 * @param condition - The Condition.
 * @param value - One of its values, as stored.
 * @returns The slot's key, e.g. `memories.patterns.condition.audience.one_to_one`.
 */
function conditionValueSlot(
  condition: PatternCondition,
  value: string,
): string {
  const valueInKey = value.replace(/[^a-z]+/g, "_");
  return `memories.patterns.condition.${condition}.${valueInKey}`;
}

/**
 * Puts where a Pattern shows and where it doesn't in words, from Copy. Who
 * the other person is reads "with …"; every other Condition reads as when.
 *
 * @param copy - The Memories page's Copy.
 * @param where - One narrowing: the Condition and its values as stored.
 * @returns The line, e.g. "It shows in a group; not one-to-one."
 */
function whereItShowsLine(copy: Copy, where: WhereItShows): string {
  const inWords = (values: string[]) =>
    values
      .map((value) =>
        readCopy(copy, conditionValueSlot(where.condition, value)),
      )
      .join(", ");
  if (conditionsAboutPeople.includes(where.condition)) {
    return fillCopy(copy, "memories.patterns.where_it_shows", {
      shows_with: inWords(where.shows_with),
      not_with: inWords(where.not_with),
    });
  }
  return fillCopy(copy, "memories.patterns.shows_when", {
    shows_when: inWords(where.shows_with),
    not_when: inWords(where.not_with),
  });
}

/**
 * One Pattern Zeph told the User about: its wording, where it shows, the
 * day Zeph told them, their quotes by part of life, and what Zeph asked
 * them to notice with how it went. Words and evidence only, never a score.
 *
 * @param props - `pattern` is the Pattern; `copy` is the Memories page's
 *   Copy; `timeZone` is the User's time zone; `isDeleting` locks the delete
 *   button; `onDelete` is called when it is pressed.
 * @returns The card.
 */
export function PatternCard({
  pattern,
  copy,
  timeZone,
  isDeleting,
  onDelete,
}: {
  pattern: Pattern;
  copy: Copy;
  timeZone?: string;
  isDeleting: boolean;
  onDelete: () => void;
}) {
  const patternsCopy = (slot: string) =>
    readCopy(copy, `memories.patterns.${slot}`);

  return (
    <MemoryCard
      deleteLabel={fillCopy(copy, "memories.patterns.delete", {
        pattern: pattern.pattern,
      })}
      isDeleting={isDeleting}
      onDelete={onDelete}
      below={
        <>
          {pattern.quote_groups.length > 0 ? (
            <div className="mt-3.5 pr-2.5">
              <div className={blockLabel}>{patternsCopy("quotes_label")}</div>
              {pattern.quote_groups.map((group) => (
                <div key={group.life_thread ?? ""} className={row}>
                  <span className={rowName}>
                    {group.life_thread ?? patternsCopy("no_thread")}
                  </span>
                  <div className={rowLines}>
                    {group.quotes.map((quote, index) => (
                      <div key={index}>
                        {fillCopy(copy, "memories.patterns.quote", {
                          quote: quote.quote,
                        })}
                        <span className="ml-2.5 text-[12px] whitespace-nowrap text-soft">
                          {formatShortCalendarDay(quote.day)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
          {pattern.predictions.length > 0 ? (
            <div className="mt-3.5 pr-2.5">
              <div className={blockLabel}>
                {patternsCopy("predictions_label")}
              </div>
              {pattern.predictions.map((prediction, index) => (
                <div key={index} className={row}>
                  <span className={rowName}>
                    {fillCopy(copy, "memories.patterns.asked_on", {
                      day: formatShortDay(prediction.made_at, timeZone),
                    })}
                  </span>
                  <div className={rowLines}>
                    <div>{prediction.wording}</div>
                    <div className="text-[13px] text-soft">
                      {readCopy(copy, outcomeSlot(prediction.outcome))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </>
      }
    >
      <div className="min-w-0">
        <p className="m-0 text-[16px] font-normal text-text">
          {pattern.pattern}
        </p>
        {pattern.where_it_shows.map((where, index) => (
          <p key={index} className="mt-1.5 mb-0 text-[14px] text-soft">
            {whereItShowsLine(copy, where)}
          </p>
        ))}
        <div className="mt-1.5">
          <span className="text-[12px] text-soft">
            {fillCopy(copy, "memories.patterns.told_on", {
              day: formatShortDay(pattern.told_at, timeZone),
            })}
          </span>
        </div>
      </div>
    </MemoryCard>
  );
}
