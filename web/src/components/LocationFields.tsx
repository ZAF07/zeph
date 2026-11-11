"use client";

import { useMemo } from "react";

import { fieldCaption, fieldLabel, inputField } from "@/components/form-styles";
import { countryOptions } from "@/lib/countries";
import { timeZoneOptions } from "@/lib/time-zones";

/**
 * The country and time zone pickers, used in onboarding and on the Account
 * page. No reason is given for asking the country.
 *
 * @param props - `country` and `timeZone` are the chosen values, with their
 *   change handlers; `countryCaption` is an optional line under the country.
 * @returns The two fields side by side.
 */
export function LocationFields({
  country,
  timeZone,
  onCountryChange,
  onTimeZoneChange,
  countryCaption,
}: {
  country: string;
  timeZone: string;
  onCountryChange: (country: string) => void;
  onTimeZoneChange: (timeZone: string) => void;
  countryCaption?: string;
}) {
  const countries = useMemo(() => countryOptions(), []);
  const timeZones = useMemo(() => timeZoneOptions(timeZone), [timeZone]);

  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(min(240px,100%),1fr))] gap-4">
      <label className={fieldLabel}>
        Country
        <select
          className={inputField}
          required
          value={country}
          onChange={(event) => onCountryChange(event.target.value)}
        >
          <option value="" disabled>
            Choose your country
          </option>
          {countries.map((option) => (
            <option key={option.code} value={option.code}>
              {option.name}
            </option>
          ))}
        </select>
        {countryCaption ? (
          <span className={fieldCaption}>{countryCaption}</span>
        ) : null}
      </label>
      <label className={fieldLabel}>
        Time zone
        <select
          className={inputField}
          required
          value={timeZone}
          onChange={(event) => onTimeZoneChange(event.target.value)}
        >
          <option value="" disabled>
            Choose your time zone
          </option>
          {timeZones.map((option) => (
            <option key={option.name} value={option.name}>
              {option.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
