"use client";

import { useCallback, useEffect, useState } from "react";

import { compactSecondaryButton } from "@/components/button-styles";
import { inputField } from "@/components/form-styles";
import { HelplineForm } from "@/components/HelplineForm";
import { LoadFailed } from "@/components/LoadFailed";
import type {
  Helpline,
  HelplineInput,
  Helplines,
  MoveDirection,
} from "@/lib/api-client";
import { countryName } from "@/lib/countries";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; helplines: Helplines };

type Editing =
  { kind: "add" } | { kind: "edit"; helpline: Helpline } | { kind: "fallback" };

type Flash = { text: string; isError: boolean };

const headings = ["Country", "Name", "Number", "Hours", "Order"];

const headCell =
  "whitespace-nowrap border-b border-line bg-subtle px-[18px] py-3.5 text-left font-mono text-[11px] font-medium uppercase tracking-[0.06em] text-ink-muted";

const cell = "px-[18px] py-3.5";

const iconButton =
  "inline-flex h-8 w-8 cursor-pointer items-center justify-center rounded-full border border-line-strong bg-transparent text-ink disabled:cursor-not-allowed disabled:opacity-40";

/**
 * Gives a Helpline's place within its country's list.
 *
 * @param helplines - Every country Helpline, by country and order.
 * @param helpline - The Helpline.
 * @returns Its position from 1, and how many its country has.
 */
function placeInCountry(
  helplines: Helpline[],
  helpline: Helpline,
): { position: number; total: number } {
  const sameCountry = helplines.filter(
    (other) => other.country === helpline.country,
  );
  return {
    position: sameCountry.findIndex((other) => other.id === helpline.id) + 1,
    total: sameCountry.length,
  };
}

/**
 * The Safety page's Helplines section: every country's Helplines, with the
 * international fallback always last. Admins add, edit, reorder and remove
 * Helplines, and edit (but never remove) the fallback.
 *
 * @returns The table and its forms, or a loading, empty or error state.
 */
export function HelplinesManager() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [countryFilter, setCountryFilter] = useState("all");
  const [editing, setEditing] = useState<Editing | null>(null);
  const [flash, setFlash] = useState<Flash | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setState({ kind: "loaded", helplines: await apiClient.listHelplines() });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  async function saveForm(input: HelplineInput) {
    if (editing?.kind === "add") {
      await apiClient.addHelpline(input);
      setFlash({ text: `Added ${input.name}.`, isError: false });
    } else if (editing?.kind === "edit") {
      await apiClient.updateHelpline(editing.helpline.id, input);
      setFlash({ text: `Saved ${input.name}.`, isError: false });
    } else {
      await apiClient.updateInternationalFallback({
        name: input.name,
        number: input.number,
        hours: input.hours,
      });
      setFlash({ text: "Saved the international fallback.", isError: false });
    }
    setEditing(null);
    await load();
  }

  async function runRowAction(
    helpline: Helpline,
    action: () => Promise<unknown>,
    successText: string | null,
  ) {
    setBusyId(helpline.id);
    setFlash(null);
    try {
      await action();
      if (successText) {
        setFlash({ text: successText, isError: false });
      }
      await load();
    } catch {
      setFlash({
        text: `Couldn’t change ${helpline.name}. Please try again.`,
        isError: true,
      });
    } finally {
      setBusyId(null);
    }
  }

  function move(helpline: Helpline, direction: MoveDirection) {
    void runRowAction(
      helpline,
      () => apiClient.moveHelpline(helpline.id, direction),
      null,
    );
  }

  function remove(helpline: Helpline) {
    if (!window.confirm(`Remove ${helpline.name}?`)) {
      return;
    }
    void runRowAction(
      helpline,
      () => apiClient.deleteHelpline(helpline.id),
      `Removed ${helpline.name}.`,
    );
  }

  if (state.kind === "loading") {
    return (
      <div
        aria-busy="true"
        aria-label="Loading Helplines"
        className="h-[320px] rounded-card border border-line bg-subtle"
      />
    );
  }

  if (state.kind === "failed") {
    return (
      <LoadFailed
        title="Couldn’t load Helplines"
        body="Zeph keeps using the last saved Helplines."
        onRetry={() => void load()}
      />
    );
  }

  const { helplines, international_fallback: fallback } = state.helplines;
  const countriesWithHelplines = [
    ...new Set(helplines.map((helpline) => helpline.country ?? "")),
  ];
  const shownHelplines = helplines.filter(
    (helpline) => countryFilter === "all" || helpline.country === countryFilter,
  );

  return (
    <section
      aria-labelledby="helplines-heading"
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-5"
    >
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h2 id="helplines-heading" className="m-0 text-[17px] font-semibold">
          Helplines
        </h2>
        <div className="flex flex-wrap items-end gap-2">
          <div className="flex flex-col gap-1 text-caption text-ink-muted">
            <label htmlFor="helpline-country-filter">Country</label>
            <select
              id="helpline-country-filter"
              className={`${inputField} min-h-10 w-auto py-2`}
              value={countryFilter}
              onChange={(event) => setCountryFilter(event.target.value)}
            >
              <option value="all">All countries</option>
              {countriesWithHelplines.map((country) => (
                <option key={country} value={country}>
                  {countryName(country)}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className={compactSecondaryButton}
            onClick={() => {
              setEditing({ kind: "add" });
              setFlash(null);
            }}
          >
            Add Helpline
          </button>
        </div>
      </div>

      {flash ? (
        <p
          role="status"
          className={`m-0 rounded-xl px-4 py-3.5 text-sm ${
            flash.isError
              ? "border border-danger-line bg-danger-tint text-danger-deep"
              : "bg-blue-tint text-blue-deep"
          }`}
        >
          {flash.text}
        </p>
      ) : null}

      {editing ? (
        <HelplineForm
          key={editing.kind === "edit" ? editing.helpline.id : editing.kind}
          title={
            editing.kind === "add"
              ? "Add Helpline"
              : editing.kind === "edit"
                ? `Edit ${editing.helpline.name}`
                : "Edit international fallback"
          }
          initial={
            editing.kind === "add"
              ? {
                  country: countryFilter === "all" ? "" : countryFilter,
                  name: "",
                  number: "",
                  hours: null,
                }
              : editing.kind === "edit"
                ? {
                    country: editing.helpline.country ?? "",
                    name: editing.helpline.name,
                    number: editing.helpline.number,
                    hours: editing.helpline.hours,
                  }
                : {
                    country: "",
                    name: fallback.name,
                    number: fallback.number,
                    hours: fallback.hours,
                  }
          }
          withCountry={editing.kind !== "fallback"}
          submitLabel={editing.kind === "add" ? "Add Helpline" : "Save"}
          onSubmit={saveForm}
          onCancel={() => setEditing(null)}
        />
      ) : null}

      {helplines.length === 0 ? (
        <div className="flex flex-col gap-1 rounded-xl border border-dashed border-line-strong px-5 py-6">
          <span className="font-semibold">No Helplines yet</span>
          <p className="m-0 text-caption text-ink-muted">
            Until you add some, every User gets the international fallback
            below. Add at least an emergency number for each launch country.
          </p>
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-xl border border-line">
        <table className="w-full min-w-[760px] border-collapse text-sm">
          <thead>
            <tr>
              {headings.map((heading) => (
                <th key={heading} scope="col" className={headCell}>
                  {heading}
                </th>
              ))}
              <th scope="col" className={headCell}>
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {shownHelplines.map((helpline) => {
              const { position, total } = placeInCountry(helplines, helpline);
              const isBusy = busyId === helpline.id;
              return (
                <tr key={helpline.id} className="border-b border-line">
                  <td className={cell}>
                    {countryName(helpline.country ?? "")}
                  </td>
                  <td className={`${cell} font-medium`}>{helpline.name}</td>
                  <td className={`${cell} tabular-nums`}>{helpline.number}</td>
                  <td className={cell}>{helpline.hours ?? "—"}</td>
                  <td className={cell}>
                    <span className="inline-flex items-center gap-1.5">
                      <span className="w-4 tabular-nums">{position}</span>
                      <button
                        type="button"
                        className={iconButton}
                        aria-label={`Move ${helpline.name} up`}
                        disabled={isBusy || position === 1}
                        onClick={() => move(helpline, "up")}
                      >
                        ↑
                      </button>
                      <button
                        type="button"
                        className={iconButton}
                        aria-label={`Move ${helpline.name} down`}
                        disabled={isBusy || position === total}
                        onClick={() => move(helpline, "down")}
                      >
                        ↓
                      </button>
                    </span>
                  </td>
                  <td className={`${cell} text-right`}>
                    <span className="inline-flex gap-1.5">
                      <button
                        type="button"
                        className={compactSecondaryButton}
                        disabled={isBusy}
                        onClick={() => {
                          setEditing({ kind: "edit", helpline });
                          setFlash(null);
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className={iconButton}
                        aria-label={`Remove ${helpline.name}`}
                        disabled={isBusy}
                        onClick={() => remove(helpline)}
                      >
                        ✕
                      </button>
                    </span>
                  </td>
                </tr>
              );
            })}
            <tr className="bg-subtle">
              <td className={`${cell} font-medium`}>International fallback</td>
              <td className={`${cell} font-medium`}>{fallback.name}</td>
              <td className={cell}>{fallback.number}</td>
              <td className={cell}>{fallback.hours ?? "—"}</td>
              <td className={`${cell} text-ink-muted`}>Always last</td>
              <td className={`${cell} text-right`}>
                <button
                  type="button"
                  className={compactSecondaryButton}
                  aria-label="Edit international fallback"
                  onClick={() => {
                    setEditing({ kind: "fallback" });
                    setFlash(null);
                  }}
                >
                  Edit
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p className="m-0 text-caption text-ink-muted">
        Shared with Users whose country has no Helplines. It can’t be removed.
      </p>
    </section>
  );
}
