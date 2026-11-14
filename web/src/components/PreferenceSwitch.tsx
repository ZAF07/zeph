"use client";

import type { ReactNode } from "react";

import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { Switch } from "@/components/Switch";
import { notAvailableText } from "@/lib/features";
import { paragraphs } from "@/lib/paragraphs";
import { useUpdatePreferences } from "@/lib/queries";

/** The User's own on/off settings that a `PreferenceSwitch` can save. */
export type SwitchPreference = "user_memory_enabled" | "photo_viewing_enabled";

/**
 * A section with a heading and a switch that saves one of the User's on/off
 * settings straight away, with the Admin-worded explanation below it.
 *
 * @param props - `preference` is the setting the switch saves; `title` is
 *   the heading and the switch's label; `enabled` is the saved setting;
 *   `available` is false when an Admin has the feature off for the User,
 *   which disables the switch; `explanation` is the Admin-worded text;
 *   `changedInChatAt` is when it was last changed in chat, if it was;
 *   `timeZone` is the User's; `children` is shown between the caption and
 *   the explanation.
 * @returns The section.
 */
export function PreferenceSwitch({
  preference,
  title,
  enabled,
  available,
  explanation,
  changedInChatAt,
  timeZone,
  children,
}: {
  preference: SwitchPreference;
  title: string;
  enabled: boolean;
  available: boolean;
  explanation: string;
  changedInChatAt: string | undefined;
  timeZone?: string;
  children?: ReactNode;
}) {
  const updatePreferences = useUpdatePreferences();
  const headingId = `${preference}-heading`;

  return (
    <section
      aria-labelledby={headingId}
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-8"
    >
      <div className="flex items-center justify-between gap-4">
        <h2 id={headingId} className="m-0 text-[17px] font-semibold">
          {title}
        </h2>
        <Switch
          label={title}
          checked={enabled}
          disabled={updatePreferences.isPending || !available}
          onChange={(next) => updatePreferences.mutate({ [preference]: next })}
        />
      </div>
      {available ? null : (
        <p className="m-0 text-sm font-medium text-ink-soft">
          {notAvailableText}
        </p>
      )}
      <ChangedInChatCaption changedAt={changedInChatAt} timeZone={timeZone} />
      {children}
      {paragraphs(explanation).map((paragraph) => (
        <p key={paragraph} className="m-0 text-[15px] text-ink-soft">
          {paragraph}
        </p>
      ))}
      {updatePreferences.isError ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          We couldn’t change that. Please try again.
        </p>
      ) : null}
    </section>
  );
}
