"use client";

import type { ReactNode } from "react";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { Switch } from "@/components/Switch";
import { type Copy, readCopy } from "@/lib/copy";
import { paragraphs } from "@/lib/paragraphs";
import { useUpdatePreferences } from "@/lib/queries";

/** The User's own on/off settings that a `PreferenceSwitch` can save. */
export type SwitchPreference =
  | "user_memory_enabled"
  | "photo_viewing_enabled"
  | "contested_gathering_enabled";

const settingParagraph = "mt-0 mb-2 max-w-[620px] text-[14px] text-soft";

/**
 * A card with a heading, the Admin-worded explanation, and a switch beside
 * them that saves one of the User's on/off settings straight away.
 *
 * @param props - `preference` is the setting the switch saves; `title` is
 *   the heading and the switch's label; `enabled` is the saved setting;
 *   `available` is false when an Admin has the feature off for the User,
 *   which disables the switch; `explanation` is the Admin-worded text;
 *   `changedInChatAt` is when it was last changed in chat, if it was;
 *   `timeZone` is the User's; `copy` holds the Account page's Copy;
 *   `children` is shown above the explanation.
 * @returns The card.
 */
export function PreferenceSwitch({
  preference,
  title,
  enabled,
  available,
  explanation,
  changedInChatAt,
  timeZone,
  copy,
  children,
}: {
  preference: SwitchPreference;
  title: string;
  enabled: boolean;
  available: boolean;
  explanation: string;
  changedInChatAt: string | undefined;
  timeZone?: string;
  copy: Copy;
  children?: ReactNode;
}) {
  const accountCopy = (slot: string) => readCopy(copy, `account.${slot}`);
  const updatePreferences = useUpdatePreferences();
  const headingId = `${preference}-heading`;

  return (
    <section
      aria-labelledby={headingId}
      className="box-border rounded-card border border-line bg-panel py-5 pr-3.5 pl-6"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2
            id={headingId}
            className="mt-0 mb-2 text-[17px] font-normal text-cream"
          >
            {title}
          </h2>
          {available ? null : (
            <p className={settingParagraph}>{accountCopy("not_available")}</p>
          )}
          {children ? <div className="mb-2">{children}</div> : null}
          {paragraphs(explanation).map((paragraph) => (
            <p key={paragraph} className={settingParagraph}>
              {paragraph}
            </p>
          ))}
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
              <SaveFailedNote>
                {accountCopy("switch_save_failed")}
              </SaveFailedNote>
            </div>
          ) : null}
        </div>
        <Switch
          label={title}
          checked={enabled}
          disabled={updatePreferences.isPending || !available}
          onChange={(next) => updatePreferences.mutate({ [preference]: next })}
        />
      </div>
    </section>
  );
}
