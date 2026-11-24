"use client";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { ChoiceSegments } from "@/components/ChoiceSegments";
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
      <div className="mt-3.5">
        <ChoiceSegments
          label={title}
          options={levels.map((level) => ({
            value: level,
            label: accountCopy(`directness.${level}`),
          }))}
          value={directness}
          layoutClassName="max-w-[640px] grid-cols-3 rounded-pill"
          disabled={updatePreferences.isPending}
          onChange={(level) => updatePreferences.mutate({ directness: level })}
        />
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
