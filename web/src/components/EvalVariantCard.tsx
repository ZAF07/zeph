import { MakeLiveControl } from "@/components/MakeLiveControl";
import { SettingValueLine } from "@/components/SettingValueLine";
import type { EvalRunState, EvalVariant } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import { describeSettingValue } from "@/lib/setting-overrides";

/** Values this long, or with line breaks, open on a click. */
const shortValueLength = 80;

/**
 * Says whether a value reads well on one line.
 *
 * @param value - The value.
 * @returns True if it is short and has no line breaks.
 */
function isShort(value: unknown): boolean {
  const text = describeSettingValue(value);
  return text.length <= shortValueLength && !text.includes("\n");
}

/**
 * One Variant of a run: the live settings, or each Setting Override as a
 * difference from the live value when the run started. It shows who made
 * it live, when, and what was applied or left out, or the Make Live button
 * on a Finished run.
 *
 * @param props - `runId` and `runState` are the run's; `variant` is the
 *   Variant; `labelOf` names a setting by its key; `thenValueOf` gives a
 *   setting's live value when the run started, or undefined while Queued.
 * @returns The Variant's card.
 */
export function EvalVariantCard({
  runId,
  runState,
  variant,
  labelOf,
  thenValueOf,
}: {
  runId: string;
  runState: EvalRunState;
  variant: EvalVariant;
  labelOf: (key: string) => string;
  thenValueOf: (key: string) => unknown;
}) {
  const keys = Object.keys(variant.setting_overrides);
  const madeLive = variant.made_live;

  return (
    <section
      aria-label={`Variant ${variant.letter}`}
      className="flex flex-col gap-2.5 rounded-xl border border-line bg-white px-[18px] py-3.5"
    >
      <h2 className="m-0 text-body font-semibold">
        Variant {variant.letter}{" "}
        <span className="font-normal text-ink-muted">
          ·{" "}
          {keys.length === 0
            ? "live settings"
            : `live settings with ${keys.length} changed`}
        </span>
      </h2>
      {keys.length > 0 ? (
        <ul className="m-0 flex list-none flex-col gap-2 p-0 text-caption">
          {keys.map((key) => {
            const then = thenValueOf(key);
            const override = variant.setting_overrides[key];
            const lines = (
              <>
                {then !== undefined ? (
                  <SettingValueLine name="Live when it started" value={then} />
                ) : null}
                <SettingValueLine
                  name={`Variant ${variant.letter}`}
                  value={override}
                />
              </>
            );
            return (
              <li key={key} className="flex flex-col gap-0.5">
                {isShort(then) && isShort(override) ? (
                  <>
                    <span className="font-medium">{labelOf(key)}</span>
                    {lines}
                  </>
                ) : (
                  <details>
                    <summary className="cursor-pointer font-medium">
                      {labelOf(key)}
                    </summary>
                    <div className="mt-1 flex flex-col gap-1">{lines}</div>
                  </details>
                )}
              </li>
            );
          })}
        </ul>
      ) : null}
      {madeLive ? (
        <div className="flex flex-col gap-0.5 rounded-lg bg-blue-tint px-3 py-2 text-caption text-blue-deep">
          <p className="m-0 font-medium">
            Made live by {madeLive.by_name ?? "an Admin"},{" "}
            {formatSavedAt(madeLive.at)}.
          </p>
          {madeLive.applied_keys.length > 0 ? (
            <p className="m-0">
              Applied: {madeLive.applied_keys.map(labelOf).join(", ")}.
            </p>
          ) : null}
          {madeLive.left_out_keys.length > 0 ? (
            <p className="m-0">
              Left out, as they changed live since the run:{" "}
              {madeLive.left_out_keys.map(labelOf).join(", ")}.
            </p>
          ) : null}
        </div>
      ) : runState === "finished" && keys.length > 0 ? (
        <MakeLiveControl
          runId={runId}
          letter={variant.letter}
          labelOf={labelOf}
        />
      ) : null}
    </section>
  );
}
