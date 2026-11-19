"use client";

import { useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { FieldRow } from "@/components/FieldRow";
import { FieldRows } from "@/components/FieldRows";
import { FieldSelect } from "@/components/FieldSelect";
import { FieldText } from "@/components/FieldText";
import { SaveFailedNote } from "@/components/SaveFailedNote";
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
      className="flex flex-col gap-3"
      onSubmit={(event) => {
        event.preventDefault();
        void submit();
      }}
    >
      <h3 className="m-0 text-[15px] font-normal text-text">{title}</h3>
      <FieldRows>
        {withCountry ? (
          <FieldRow title="Country" htmlFor="helpline-country">
            <FieldSelect
              id="helpline-country"
              value={values.country}
              options={[
                { value: "", label: "Choose a country" },
                ...countries.map((country) => ({
                  value: country.code,
                  label: country.name,
                })),
              ]}
              onChange={(value) => edit("country", value)}
            />
          </FieldRow>
        ) : null}
        <FieldRow title="Name" htmlFor="helpline-name">
          <FieldText
            id="helpline-name"
            value={values.name}
            onChange={(value) => edit("name", value)}
          />
        </FieldRow>
        <FieldRow
          title="Number"
          caption="A phone number or web address."
          htmlFor="helpline-number"
        >
          <FieldText
            id="helpline-number"
            value={values.number}
            onChange={(value) => edit("number", value)}
          />
        </FieldRow>
        <FieldRow title="Hours" caption="Optional." htmlFor="helpline-hours">
          <FieldText
            id="helpline-hours"
            placeholder="e.g. 24 hours"
            value={values.hours}
            onChange={(value) => edit("hours", value)}
          />
        </FieldRow>
      </FieldRows>
      {error ? <SaveFailedNote>{error}</SaveFailedNote> : null}
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
