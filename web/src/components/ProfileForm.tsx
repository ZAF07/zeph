"use client";

import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { ChangedInChatCaption } from "@/components/ChangedInChatCaption";
import { fieldCaption, fieldLabel, inputField } from "@/components/form-styles";
import { LocationFields } from "@/components/LocationFields";
import type { Me } from "@/lib/api-client";
import { useUpdatePreferences } from "@/lib/queries";

/**
 * The Profile section: what Zeph calls the User, their email, country and
 * time zone, saved with one button.
 *
 * @param props - `me` is the signed-in User as last loaded.
 * @returns The form.
 */
export function ProfileForm({ me }: { me: Me }) {
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
      className="flex flex-col gap-5 rounded-card border border-line bg-white p-8"
    >
      <h2 id="profile-heading" className="m-0 text-[17px] font-semibold">
        Profile
      </h2>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(min(240px,100%),1fr))] gap-4">
        <label className={fieldLabel}>
          What Zeph calls you
          <input
            className={inputField}
            type="text"
            maxLength={100}
            value={name}
            onChange={(event) => clearSavedOnEdit(setName)(event.target.value)}
          />
        </label>
        <div className={fieldLabel}>
          <span>Email</span>
          <span className={`${inputField} flex items-center text-ink-soft`}>
            {me.email ?? "—"}
          </span>
          <span className={fieldCaption}>From your sign-in</span>
        </div>
      </div>
      <LocationFields
        country={country}
        timeZone={timeZone}
        onCountryChange={clearSavedOnEdit(setCountry)}
        onTimeZoneChange={clearSavedOnEdit(setTimeZone)}
        timeZoneNote={
          <ChangedInChatCaption
            changedAt={me.changed_in_chat.time_zone}
            timeZone={me.time_zone ?? undefined}
          />
        }
      />
      <div className="flex flex-wrap items-center gap-3">
        <button type="submit" className={primaryButton} disabled={!canSave}>
          {updatePreferences.isPending ? "Saving…" : "Save changes"}
        </button>
        {updatePreferences.isSuccess ? (
          <p role="status" className="m-0 text-sm text-blue-deep">
            Saved
          </p>
        ) : null}
        {updatePreferences.isError ? (
          <p role="alert" className="m-0 text-sm text-danger-deep">
            We couldn’t save that. Please try again.
          </p>
        ) : null}
      </div>
    </form>
  );
}
