"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { compactSecondaryButton } from "@/components/button-styles";
import { inputField } from "@/components/form-styles";
import { HelplineForm } from "@/components/HelplineForm";
import { LoadFailed } from "@/components/LoadFailed";
import type {
  ApiClient,
  Helpline,
  HelplineInput,
  MoveDirection,
} from "@/lib/api-client";
import { countryName } from "@/lib/countries";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

type Editing =
  { kind: "add" } | { kind: "edit"; helpline: Helpline } | { kind: "fallback" };

type Flash = { text: string; isError: boolean };

/** What the Helpline form shows and does for one kind of edit. */
type FormSetup = {
  key: string;
  title: string;
  initial: HelplineInput;
  withCountry: boolean;
  submitLabel: string;
  save: (input: HelplineInput) => Promise<string>;
};

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
 * Describes the Helpline form for adding a Helpline, editing one, or editing
 * the international fallback.
 *
 * @param editing - What is being edited.
 * @param countryFilter - The chosen country filter; a new Helpline starts in
 *   that country.
 * @param fallback - The international fallback.
 * @param apiClient - Saves the form.
 * @returns The form's title, starting values and labels, and `save`, which
 *   saves and returns the message to show.
 */
function formSetup(
  editing: Editing,
  countryFilter: string,
  fallback: Helpline,
  apiClient: Pick<
    ApiClient,
    "addHelpline" | "updateHelpline" | "updateInternationalFallback"
  >,
): FormSetup {
  if (editing.kind === "add") {
    return {
      key: "add",
      title: "Add Helpline",
      initial: {
        country: countryFilter === "all" ? "" : countryFilter,
        name: "",
        number: "",
        hours: null,
      },
      withCountry: true,
      submitLabel: "Add Helpline",
      save: async (input) => {
        await apiClient.addHelpline(input);
        return `Added ${input.name}.`;
      },
    };
  }
  if (editing.kind === "edit") {
    const { helpline } = editing;
    return {
      key: helpline.id,
      title: `Edit ${helpline.name}`,
      initial: {
        country: helpline.country ?? "",
        name: helpline.name,
        number: helpline.number,
        hours: helpline.hours,
      },
      withCountry: true,
      submitLabel: "Save",
      save: async (input) => {
        await apiClient.updateHelpline(helpline.id, input);
        return `Saved ${input.name}.`;
      },
    };
  }
  return {
    key: "fallback",
    title: "Edit international fallback",
    initial: {
      country: "",
      name: fallback.name,
      number: fallback.number,
      hours: fallback.hours,
    },
    withCountry: false,
    submitLabel: "Save",
    save: async ({ name, number, hours }) => {
      await apiClient.updateInternationalFallback({ name, number, hours });
      return "Saved the international fallback.";
    },
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
  const queryClient = useQueryClient();
  const [countryFilter, setCountryFilter] = useState("all");
  const [editing, setEditing] = useState<Editing | null>(null);
  const [flash, setFlash] = useState<Flash | null>(null);

  const helplinesQuery = useQuery({
    queryKey: queryKeys.helplines,
    queryFn: () => apiClient.listHelplines(),
  });

  async function reloadHelplines() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.helplines });
  }

  const rowAction = useMutation({
    mutationFn: async ({
      action,
    }: {
      target: Helpline;
      action: () => Promise<unknown>;
      successText: string | null;
    }) => {
      await action();
      await reloadHelplines();
    },
    onMutate: () => setFlash(null),
    onSuccess: (_, { successText }) => {
      if (successText) {
        setFlash({ text: successText, isError: false });
      }
    },
    onError: (_, { target }) =>
      setFlash({
        text: `Couldn’t change ${target.name}. Please try again.`,
        isError: true,
      }),
  });
  const busyId = rowAction.isPending ? rowAction.variables.target.id : null;

  function runRowAction(
    target: Helpline,
    action: () => Promise<unknown>,
    successText: string | null,
  ) {
    rowAction.mutate({ target, action, successText });
  }

  function move(helpline: Helpline, direction: MoveDirection) {
    runRowAction(
      helpline,
      () => apiClient.moveHelpline(helpline.id, direction),
      null,
    );
  }

  function remove(helpline: Helpline) {
    if (!window.confirm(`Remove ${helpline.name}?`)) {
      return;
    }
    runRowAction(
      helpline,
      () => apiClient.deleteHelpline(helpline.id),
      `Removed ${helpline.name}.`,
    );
  }

  if (!helplinesQuery.data) {
    if (helplinesQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Helplines"
          body="Zeph keeps using the last saved Helplines."
          onRetry={() => void helplinesQuery.refetch()}
        />
      );
    }
    return (
      <div
        aria-busy="true"
        aria-label="Loading Helplines"
        className="h-[320px] rounded-card border border-line bg-subtle"
      />
    );
  }

  const { helplines, international_fallback: fallback } = helplinesQuery.data;
  const countriesWithHelplines = [
    ...new Set(helplines.map((helpline) => helpline.country ?? "")),
  ];
  const form = editing
    ? formSetup(editing, countryFilter, fallback, apiClient)
    : null;
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

      {form ? (
        <HelplineForm
          key={form.key}
          title={form.title}
          initial={form.initial}
          withCountry={form.withCountry}
          submitLabel={form.submitLabel}
          onSubmit={async (input) => {
            const message = await form.save(input);
            setFlash({ text: message, isError: false });
            setEditing(null);
            await reloadHelplines();
          }}
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
