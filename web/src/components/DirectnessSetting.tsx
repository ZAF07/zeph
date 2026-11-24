"use client";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { Directness } from "@/lib/api-client";
import { type Copy, readCopy } from "@/lib/copy";
import { useUpdatePreferences } from "@/lib/queries";

const levels: Directness[] = ["gentle", "balanced", "direct"];

/**
 * The Account page's "How direct Zeph is" card: a heading, the help text
 * and one row of three equal segments, gentle, balanced and direct, that
 * saves the picked one straight away. The picked one is the cream pill.
 *
 * @param props - `directness` is the saved setting; `changedInChatAt` is
 *   when it was last changed in chat, if it was; `timeZone` is the User's;
 *   `copy` holds the Account page's Copy.
 * @returns The card.
 */
export function DirectnessSetting({
  directness,
  changedInChatAt,
  timeZone,
  copy,
}: {
  directness: Directness;
  changedInChatAt: string | undefined;
  timeZone?: string;
  copy: Copy;
}) {
  const accountCopy = (slot: string) => readCopy(copy, `account.${slot}`);
  const updatePreferences = useUpdatePreferences();
  const title = accountCopy("directness.title");

  return (
    <section
      aria-labelledby="directness-heading"
      className="box-border rounded-card border border-line bg-panel px-6 py-5"
    >
      <h2
        id="directness-heading"
        className="mt-0 mb-2 text-[17px] font-normal text-cream"
      >
        {title}
      </h2>
      <p className="mt-0 mb-2 max-w-[620px] text-[14px] text-soft">
        {accountCopy("directness.help")}
      </p>
      <div
        role="group"
        aria-label={title}
        className="mt-3.5 box-border grid w-full max-w-[640px] grid-cols-3 gap-1 rounded-pill border border-line bg-bg-deep p-1"
      >
        {levels.map((level) => {
          const isPicked = level === directness;
          return (
            <button
              key={level}
              type="button"
              aria-pressed={isPicked}
              disabled={updatePreferences.isPending}
              onClick={() => updatePreferences.mutate({ directness: level })}
              className={`min-h-12 cursor-pointer rounded-pill border-0 px-2 py-1 text-center text-[13px] leading-[1.2] disabled:cursor-not-allowed ${
                isPicked
                  ? "bg-cream font-medium text-ink"
                  : "bg-transparent font-light text-soft"
              }`}
            >
              {accountCopy(`directness.${level}`)}
            </button>
          );
        })}
      </div>
      {changedInChatAt ? (
        <div className="mt-2">
          <ChangedInChatCaption
            changedAt={changedInChatAt}
            timeZone={timeZone}
            text={accountCopy("changed_in_chat")}
          />
        </div>
      ) : null}
      {updatePreferences.isError ? (
        <div className="mt-2">
          <SaveFailedNote>{accountCopy("switch_save_failed")}</SaveFailedNote>
        </div>
      ) : null}
    </section>
  );
}
