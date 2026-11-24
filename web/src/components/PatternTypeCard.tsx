import { CardTag } from "@/components/CardTag";
import { FoldingCard } from "@/components/FoldingCard";
import { PatternTypeEntry } from "@/components/PatternTypeEntry";
import { PatternTypeGroup } from "@/components/PatternTypeGroup";
import { PatternTypeLine } from "@/components/PatternTypeLine";
import type { PatternSign, PatternType } from "@/lib/api-client";
import { formatDay } from "@/lib/dates";
import {
  areaLabels,
  describeSignature,
  describeStatus,
  evidenceLabels,
  partLabels,
  statusLabels,
  strengthLabels,
} from "@/lib/pattern-catalog";

/**
 * Draws signs as rows: each sign's text, its ID under it, and its strength
 * and the part it shows as tags.
 *
 * @param signs - The signs, in order.
 * @returns The rows.
 */
function signRows(signs: PatternSign[]) {
  return signs.map((sign) => (
    <PatternTypeEntry
      key={sign.id}
      title={sign.text}
      detail={sign.id}
      tags={
        <>
          <CardTag>{strengthLabels[sign.strength]}</CardTag>
          <CardTag>{partLabels[sign.part]}</CardTag>
        </>
      }
    />
  ));
}

/**
 * One Pattern Type as a folding card of the Pattern Catalog. The folded row
 * shows its name, its if / then / function line, its area, status and
 * version. Open, it shows every detail in groups: what it is, signs, signs
 * against, look-alikes, exclusions, wording, and its numbers and status.
 * Nothing on it can be edited: Pattern Types change only in their files
 * (ADR-0025).
 *
 * @param props - `patternType` is the Pattern Type; `isOpen` and `onToggle`
 *   open and fold the card.
 * @returns The card.
 */
export function PatternTypeCard({
  patternType,
  isOpen,
  onToggle,
}: {
  patternType: PatternType;
  isOpen: boolean;
  onToggle: () => void;
}) {
  const groupId = (group: string) => `${patternType.id}-${group}`;
  return (
    <FoldingCard
      title={patternType.name}
      summary={describeSignature(patternType)}
      tags={
        <>
          <CardTag>{areaLabels[patternType.area]}</CardTag>
          <CardTag>{statusLabels[patternType.status]}</CardTag>
        </>
      }
      meta={`v${patternType.version}`}
      isDirty={false}
      isOpen={isOpen}
      onToggle={onToggle}
    >
      <PatternTypeGroup id={groupId("what")} title="What it is">
        <PatternTypeLine label="ID">{patternType.id}</PatternTypeLine>
        <PatternTypeLine label="Definition">
          {patternType.definition}
        </PatternTypeLine>
        <PatternTypeLine label="If">{patternType.if_situation}</PatternTypeLine>
        <PatternTypeLine label="Then">
          {patternType.then_behaviour}
        </PatternTypeLine>
        <PatternTypeLine label="Function">
          {patternType.function}
        </PatternTypeLine>
        <PatternTypeLine label="Based on">
          {patternType.frameworks.join("; ")}
        </PatternTypeLine>
      </PatternTypeGroup>
      <PatternTypeGroup
        id={groupId("signs")}
        title="Signs"
        caption="What counts for it. Each has a strength and the part of the Pattern it shows."
      >
        {signRows(patternType.signs)}
      </PatternTypeGroup>
      <PatternTypeGroup
        id={groupId("signs-against")}
        title="Signs against"
        caption="What counts against it."
      >
        {signRows(patternType.signs_against)}
      </PatternTypeGroup>
      <PatternTypeGroup
        id={groupId("look-alikes")}
        title="Look-alikes"
        caption="What it can be mistaken for, and what tells them apart."
      >
        {patternType.look_alikes.map((lookAlike, index) => (
          <PatternTypeEntry
            key={`${index}-${lookAlike.name}`}
            title={lookAlike.name}
            detail={lookAlike.tells_apart}
            tags={
              <CardTag>
                {lookAlike.pattern_type_id ?? "Not a Pattern Type"}
              </CardTag>
            }
          />
        ))}
        <PatternTypeEntry
          title="What anyone would do"
          detail={patternType.anyone_would}
          tags={<CardTag>Carries no weight</CardTag>}
        />
      </PatternTypeGroup>
      <PatternTypeGroup
        id={groupId("exclusions")}
        title="Exclusions"
        caption="When it must not be shared, and what happens to evidence from then."
      >
        {patternType.exclusions.map((exclusion, index) => (
          <PatternTypeEntry
            key={`${index}-${exclusion.text}`}
            title={exclusion.text}
            tags={<CardTag>{evidenceLabels[exclusion.evidence]}</CardTag>}
          />
        ))}
        {patternType.exclusions.length === 0 ? (
          <PatternTypeEntry title="None" />
        ) : null}
      </PatternTypeGroup>
      <PatternTypeGroup
        id={groupId("wording")}
        title="Wording"
        caption="What Zeph words a shared Pattern and its Prediction from."
      >
        <PatternTypeLine label="Pattern">
          {patternType.approved_wording}
        </PatternTypeLine>
        <PatternTypeLine label="Prediction">
          {patternType.prediction_wording}
        </PatternTypeLine>
      </PatternTypeGroup>
      <PatternTypeGroup id={groupId("status")} title="Numbers and status">
        <PatternTypeLine label="Situations">
          {patternType.numbers.situations_needed} needed
        </PatternTypeLine>
        <PatternTypeLine label="Base rate">
          {patternType.numbers.base_rate}
        </PatternTypeLine>
        <PatternTypeLine label="Status">
          {describeStatus(patternType)}
        </PatternTypeLine>
        <PatternTypeLine label="Version">
          {patternType.version}, loaded {formatDay(patternType.loaded_at)}
        </PatternTypeLine>
        <PatternTypeLine label="Also kept">
          {patternType.other_versions.length > 0
            ? patternType.other_versions.join(", ")
            : "No other versions"}
        </PatternTypeLine>
      </PatternTypeGroup>
    </FoldingCard>
  );
}
