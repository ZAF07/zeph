"use client";

import { useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { fieldCaption, fieldLabel, inputField } from "@/components/form-styles";
import { ApiError, type HelplineInput } from "@/lib/api-client";
import { countryOptions } from "@/lib/countries";

const countries = countryOptions();

/**
 * The form for adding or editing a Helpline, or editing the international
 * fallback (which has no country).
 *
 * @param props - `title` heads the form; `initial` fills it; `withCountry`
 *   shows the country field; `submitLabel` names the save button;
 *   `onSubmit` saves and rejects if the backend refuses; `onCancel` closes
 *   it.
 * @returns The form.
 */
export function HelplineForm({
  title,
  initial,
  withCountry,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  title: string;
  initial: HelplineInput;
  withCountry: boolean;
  submitLabel: string;
  onSubmit: (helpline: HelplineInput) => Promise<void>;
  onCancel: () => void;
}) {
  const [values, setValues] = useState({
    ...initial,
    hours: initial.hours ?? "",
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isComplete =
    values.name.trim() !== "" &&
    values.number.trim() !== "" &&
    (!withCountry || values.country !== "");

  function edit(field: keyof typeof values, value: string) {
    setValues({ ...values, [field]: value });
    setError(null);
  }

  async function submit() {
    setIsSaving(true);
    setError(null);
    try {
      await onSubmit({
        country: values.country,
        name: values.name,
        number: values.number,
        hours: values.hours.trim() === "" ? null : values.hours,
      });
    } catch (failure) {
      setError(
        failure instanceof ApiError && failure.status === 422 && failure.detail
          ? failure.detail
          : "Couldn’t save the Helpline. Please try again.",
      );
      setIsSaving(false);
    }
  }

  return (
    <form
      aria-label={title}
      className="flex flex-col gap-4 rounded-xl border border-line bg-subtle p-4"
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <h3 className="m-0 text-[15px] font-semibold">{title}</h3>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-3">
        {withCountry ? (
          <div className={fieldLabel}>
            <label htmlFor="helpline-country">Country</label>
            <select
              id="helpline-country"
              className={inputField}
              value={values.country}
              onChange={(event) => edit("country", event.target.value)}
            >
              <option value="">Choose a country</option>
              {countries.map((country) => (
                <option key={country.code} value={country.code}>
                  {country.name}
                </option>
              ))}
            </select>
          </div>
        ) : null}
        <div className={fieldLabel}>
          <label htmlFor="helpline-name">Name</label>
          <input
            id="helpline-name"
            className={inputField}
            value={values.name}
            onChange={(event) => edit("name", event.target.value)}
          />
        </div>
        <div className={fieldLabel}>
          <label htmlFor="helpline-number">Number</label>
          <input
            id="helpline-number"
            className={inputField}
            aria-describedby="helpline-number-caption"
            value={values.number}
            onChange={(event) => edit("number", event.target.value)}
          />
          <span id="helpline-number-caption" className={fieldCaption}>
            A phone number or web address.
          </span>
        </div>
        <div className={fieldLabel}>
          <label htmlFor="helpline-hours">Hours</label>
          <input
            id="helpline-hours"
            className={inputField}
            aria-describedby="helpline-hours-caption"
            placeholder="e.g. 24 hours"
            value={values.hours}
            onChange={(event) => edit("hours", event.target.value)}
          />
          <span id="helpline-hours-caption" className={fieldCaption}>
            Optional.
          </span>
        </div>
      </div>
      {error ? (
        <p
          role="alert"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          {error}
        </p>
      ) : null}
      <div className="flex flex-wrap justify-end gap-2">
        <button type="button" className={secondaryButton} onClick={onCancel}>
          Cancel
        </button>
        <button
          type="submit"
          className={primaryButton}
          disabled={!isComplete || isSaving}
        >
          {isSaving ? "Saving…" : submitLabel}
        </button>
      </div>
    </form>
  );
}
