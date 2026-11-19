import { CardCheckbox } from "@/components/CardCheckbox";
import { CardTextField } from "@/components/CardTextField";
import { FieldRow } from "@/components/FieldRow";
import type { Move, NeedInput } from "@/lib/api-client";

/**
 * A Need's fields inside its card or the add box: name, "when it fits",
 * "how to reply", and a field row of the Moves it rules out.
 *
 * @param props - `value` is the Need as edited; `moves` are every Move, to
 *   rule out; `onChange` gets the edited Need.
 * @returns The fields.
 */
export function NeedFields({
  value,
  moves,
  onChange,
}: {
  value: NeedInput;
  moves: Move[];
  onChange: (value: NeedInput) => void;
}) {
  function toggleRuledOut(moveId: string, isRuledOut: boolean) {
    const ruledOut = new Set(value.ruled_out_move_ids);
    if (isRuledOut) {
      ruledOut.add(moveId);
    } else {
      ruledOut.delete(moveId);
    }
    onChange({
      ...value,
      ruled_out_move_ids: moves
        .map((move) => move.id)
        .filter((id) => ruledOut.has(id)),
    });
  }

  return (
    <>
      <CardTextField
        label="Name"
        placeholder="e.g. Be heard"
        value={value.name}
        onChange={(name) => onChange({ ...value, name })}
      />
      <CardTextField
        label="When it fits"
        hint="Zeph reads this to pick a Need."
        value={value.when_it_fits}
        multiline
        onChange={(whenItFits) =>
          onChange({ ...value, when_it_fits: whenItFits })
        }
      />
      <CardTextField
        label="How to reply"
        hint="Goes into the reply when picked."
        value={value.how_to_reply}
        multiline
        onChange={(howToReply) =>
          onChange({ ...value, how_to_reply: howToReply })
        }
      />
      <ul className="m-0 list-none p-0">
        <FieldRow
          title="Ruled-out Moves"
          caption="Never picked with this Need."
        >
          {moves.length === 0 ? (
            <span className="text-[13px] text-soft">No Moves yet.</span>
          ) : (
            <span
              role="group"
              aria-label="Ruled-out Moves"
              className="flex flex-wrap justify-end gap-x-4"
            >
              {moves.map((move) => (
                <CardCheckbox
                  key={move.id}
                  label={move.name}
                  checked={value.ruled_out_move_ids.includes(move.id)}
                  onChange={(checked) => toggleRuledOut(move.id, checked)}
                />
              ))}
            </span>
          )}
        </FieldRow>
      </ul>
    </>
  );
}
