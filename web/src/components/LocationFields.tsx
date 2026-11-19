"use client";

import { useMemo, type ReactNode } from "react";

import { countryOptions } from "@/lib/countries";
import { timeZoneOptions } from "@/lib/time-zones";

const locationLabel = "flex min-w-0 flex-[1_1_240px] flex-col gap-1.5";
const locationName = "text-[13px] text-soft";
const selectBox = "relative flex";
const selectField =
  "box-border min-h-[46px] w-full cursor-pointer appearance-none rounded-input border border-line-strong bg-bg-deep pl-3.5 pr-[34px] text-[15px] text-text";
const selectChevron =
  "pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-soft";
const locationCaption = "text-[12px] text-soft";

/** The words on the pickers, given by the page that shows them. */
export type LocationLabels = {
  country: string;
  chooseCountry: string;
  timeZone: string;
  chooseTimeZone: string;
};

/**
 * The chevron drawn at the right of each picker.
 *
 * @returns The chevron icon.
 */
function Chevron() {
  return (
    <svg
      aria-hidden="true"
      width="12"
      height="8"
      viewBox="0 0 12 8"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      className={selectChevron}
    >
      <path d="M1 1.5l5 5 5-5" />
    </svg>
  );
}

/**
 * The country and time zone pickers, used in onboarding and on the Account
 * page. No reason is given for asking the country.
 *
 * @param props - `labels` are the pickers' words, from the page that shows
 *   them; `country` and `timeZone` are the chosen values, with their
 *   change handlers; `countryCaption` is an optional line under the country,
 *   `timeZoneNote` an optional line under the time zone, and `inline` drops
 *   their own row so they wrap with the fields around them.
 * @returns The two fields side by side.
 */
export function LocationFields({
  labels,
  country,
  timeZone,
  onCountryChange,
  onTimeZoneChange,
  countryCaption,
  timeZoneNote,
  inline = false,
}: {
  labels: LocationLabels;
  country: string;
  timeZone: string;
  onCountryChange: (country: string) => void;
  onTimeZoneChange: (timeZone: string) => void;
  countryCaption?: string;
  timeZoneNote?: ReactNode;
  inline?: boolean;
}) {
  const countries = useMemo(() => countryOptions(), []);
  const timeZones = useMemo(() => timeZoneOptions(timeZone), [timeZone]);

  return (
    <div className={inline ? "contents" : "flex flex-wrap gap-4"}>
      <label className={locationLabel}>
        <span className={locationName}>{labels.country}</span>
        <span className={selectBox}>
          <select
            className={selectField}
            required
            value={country}
            onChange={(event) => onCountryChange(event.target.value)}
          >
            <option value="" disabled>
              {labels.chooseCountry}
            </option>
            {countries.map((option) => (
              <option key={option.code} value={option.code}>
                {option.name}
              </option>
            ))}
          </select>
          <Chevron />
        </span>
        {countryCaption ? (
          <span className={locationCaption}>{countryCaption}</span>
        ) : null}
      </label>
      <label className={locationLabel}>
        <span className={locationName}>{labels.timeZone}</span>
        <span className={selectBox}>
          <select
            className={selectField}
            required
            value={timeZone}
            onChange={(event) => onTimeZoneChange(event.target.value)}
          >
            <option value="" disabled>
              {labels.chooseTimeZone}
            </option>
            {timeZones.map((option) => (
              <option key={option.name} value={option.name}>
                {option.label}
              </option>
            ))}
          </select>
          <Chevron />
        </span>
        {timeZoneNote}
      </label>
    </div>
  );
}
