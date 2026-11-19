"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { DataTable } from "@/components/DataTable";
import { EmptyState } from "@/components/EmptyState";
import { FieldSelect } from "@/components/FieldSelect";
import { FormSectionHeading } from "@/components/FormSectionHeading";
import { HelplineForm } from "@/components/HelplineForm";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { SavedNote } from "@/components/SavedNote";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { TableColumn } from "@/components/TableCards";
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

/** One row of the table: a country's Helpline, or the international fallback. */
type HelplineRow =
  | { kind: "helpline"; helpline: Helpline }
  | { kind: "fallback"; helpline: Helpline };

const iconButton =
  "inline-flex size-11 cursor-pointer items-center justify-center rounded-pill border border-line-strong bg-transparent text-text disabled:cursor-not-allowed disabled:text-mute";

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
  const [removing, setRemoving] = useState<Helpline | null>(null);

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
    setRemoving(null);
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
    return <LoadingPanel shape="card" label="Loading Helplines" />;
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

  const rows: HelplineRow[] = [
    ...shownHelplines.map((helpline) => ({
      kind: "helpline" as const,
      helpline,
    })),
    { kind: "fallback", helpline: fallback },
  ];
  const columns: TableColumn<HelplineRow>[] = [
    {
      heading: "Country",
      cell: (row) =>
        row.kind === "fallback"
          ? "International fallback"
          : countryName(row.helpline.country ?? ""),
    },
    { heading: "Name", isMain: true, cell: (row) => row.helpline.name },
    {
      heading: "Number",
      cell: (row) => (
        <span className="tabular-nums">{row.helpline.number}</span>
      ),
    },
    { heading: "Hours", cell: (row) => row.helpline.hours ?? "—" },
    {
      heading: "Order",
      cell: (row) => {
        if (row.kind === "fallback") {
          return <span className="text-soft">Always last</span>;
        }
        const { helpline } = row;
        const { position, total } = placeInCountry(helplines, helpline);
        const isBusy = busyId === helpline.id;
        return (
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
        );
      },
    },
    {
      heading: "Actions",
      cell: (row) => {
        if (row.kind === "fallback") {
          return (
            <button
              type="button"
              className={secondaryButton}
              aria-label="Edit international fallback"
              onClick={() => {
                setEditing({ kind: "fallback" });
                setFlash(null);
              }}
            >
              Edit
            </button>
          );
        }
        const { helpline } = row;
        const isBusy = busyId === helpline.id;
        return (
          <span className="inline-flex gap-1.5">
            <button
              type="button"
              className={secondaryButton}
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
              onClick={() => setRemoving(helpline)}
            >
              ✕
            </button>
          </span>
        );
      },
    },
  ];

  return (
    <section
      aria-labelledby="helplines-heading"
      className="flex flex-col gap-3"
    >
      <div className="flex flex-wrap items-end justify-between gap-3">
        <FormSectionHeading id="helplines-heading" title="Helplines" />
        <div className="flex flex-wrap items-end gap-2">
          <div className="flex w-[240px] flex-col gap-1 text-[13px] text-soft">
            <label htmlFor="helpline-country-filter">Country</label>
            <FieldSelect
              id="helpline-country-filter"
              value={countryFilter}
              options={[
                { value: "all", label: "All countries" },
                ...countriesWithHelplines.map((country) => ({
                  value: country,
                  label: countryName(country),
                })),
              ]}
              onChange={setCountryFilter}
            />
          </div>
          <button
            type="button"
            className={secondaryButton}
            onClick={() => {
              setEditing({ kind: "add" });
              setFlash(null);
            }}
          >
            Add Helpline
          </button>
        </div>
      </div>

      {flash?.isError ? <SaveFailedNote>{flash.text}</SaveFailedNote> : null}
      {flash && !flash.isError ? <SavedNote>{flash.text}</SavedNote> : null}

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
        <EmptyState
          title="No Helplines yet"
          body="Until you add some, every User gets the international fallback below. Add at least an emergency number for each launch country."
        />
      ) : null}

      <DataTable
        columns={columns}
        rows={rows}
        rowKey={(row) =>
          row.kind === "fallback" ? "fallback" : row.helpline.id
        }
        minWidthClass="min-w-[760px]"
      />
      <p className="m-0 text-[13px] text-soft">
        Shared with Users whose country has no Helplines. It can’t be removed.
      </p>
      {removing ? (
        <ConfirmDialog
          open
          title={`Remove ${removing.name}?`}
          body="Users in its country stop being shown it. You can add it again later."
          cancelLabel="Keep it"
          confirmLabel="Remove"
          onConfirm={() => remove(removing)}
          onCancel={() => setRemoving(null)}
        />
      ) : null}
    </section>
  );
}
