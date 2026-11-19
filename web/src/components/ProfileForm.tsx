"use client";

import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { LocationFields } from "@/components/LocationFields";
import { SavedNote } from "@/components/SavedNote";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { Me } from "@/lib/api-client";
import { type Copy, readCopy } from "@/lib/copy";
import { useUpdatePreferences } from "@/lib/queries";

const profileLabel = "flex min-w-0 flex-[1_1_240px] flex-col gap-1.5";
const profileName = "text-[13px] text-soft";
const profileBox =
  "box-border flex min-h-[46px] w-full items-center rounded-input border bg-bg-deep px-3.5 text-[15px]";

/**
 * The Profile section: what Zeph calls the User, their email, country and
 * time zone, saved with one button.
 *
 * @param props - `me` is the signed-in User as last loaded; `copy` holds
 *   the Account page's Copy and onboarding's location labels.
 * @returns The form.
 */
export function ProfileForm({ me, copy }: { me: Me; copy: Copy }) {
  const accountCopy = (slot: string) => readCopy(copy, `account.${slot}`);
  const locationCopy = (slot: string) =>
    readCopy(copy, `onboarding.location.${slot}`);
  const updatePreferences = useUpdatePreferences();
  const [name, setName] = useState(me.name ?? "");
  const [country, setCountry] = useState(me.country ?? "");
  const [timeZone, setTimeZone] = useState(me.time_zone ?? "");

  const canSave =
    name.trim() !== "" &&
    country !== "" &&
    timeZone !== "" &&
    !updatePreferences.isPending;

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSave) {
      return;
    }
    updatePreferences.mutate({
      name: name.trim(),
      country,
      time_zone: timeZone,
    });
  }

  function clearSavedOnEdit<T>(setter: (value: T) => void) {
    return (value: T) => {
      setter(value);
      updatePreferences.reset();
    };
  }

  return (
    <form
      aria-labelledby="profile-heading"
      onSubmit={save}
      className="box-border rounded-card border border-line bg-panel px-6 py-[22px]"
    >
      <h2
        id="profile-heading"
        className="mt-0 mb-[14px] text-[17px] font-normal text-cream"
      >
        {accountCopy("profile.heading")}
      </h2>
      <div className="flex flex-wrap gap-4">
        <label className={profileLabel}>
          <span className={profileName}>
            {accountCopy("profile.name_label")}
          </span>
          <input
            className={`${profileBox} border-line-strong text-text`}
            type="text"
            maxLength={100}
            value={name}
            onChange={(event) => clearSavedOnEdit(setName)(event.target.value)}
          />
        </label>
        <div className={profileLabel}>
          <span className={profileName}>
            {accountCopy("profile.email_label")}
          </span>
          <span className={`${profileBox} border-line text-soft`}>
            {me.email ?? accountCopy("profile.no_email")}
          </span>
          <span className="text-[12px] text-soft">
            {accountCopy("profile.email_note")}
          </span>
        </div>
        <LocationFields
          inline
          labels={{
            country: locationCopy("country_label"),
            chooseCountry: locationCopy("country_choose"),
            timeZone: locationCopy("time_zone_label"),
            chooseTimeZone: locationCopy("time_zone_choose"),
          }}
          country={country}
          timeZone={timeZone}
          onCountryChange={clearSavedOnEdit(setCountry)}
          onTimeZoneChange={clearSavedOnEdit(setTimeZone)}
          timeZoneNote={
            <ChangedInChatCaption
              changedAt={me.changed_in_chat.time_zone}
              timeZone={me.time_zone ?? undefined}
              text={accountCopy("changed_in_chat")}
            />
          }
        />
      </div>
      <div className="mt-[18px] flex flex-wrap items-center gap-3">
        <button type="submit" className={primaryButton} disabled={!canSave}>
          {updatePreferences.isPending
            ? accountCopy("profile.saving")
            : accountCopy("profile.save")}
        </button>
        {updatePreferences.isSuccess ? (
          <SavedNote>{accountCopy("profile.saved")}</SavedNote>
        ) : null}
        {updatePreferences.isError ? (
          <SaveFailedNote>{accountCopy("profile.save_failed")}</SaveFailedNote>
        ) : null}
      </div>
    </form>
  );
}
