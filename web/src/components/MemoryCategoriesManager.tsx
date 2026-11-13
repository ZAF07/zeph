"use client";

import { useCallback, useEffect, useState } from "react";

import {
  compactSecondaryButton,
  primaryButton,
} from "@/components/button-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { MemoryCategoryForm } from "@/components/MemoryCategoryForm";
import { Switch } from "@/components/Switch";
import {
  ApiError,
  type MemoryCategoryInput,
  type MemoryCategoryOverview,
} from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; categories: MemoryCategoryOverview[] };

type Editing =
  { kind: "add" } | { kind: "edit"; category: MemoryCategoryOverview };

type Flash = { text: string; isError: boolean };

const emptyCategory: MemoryCategoryInput = {
  name: "",
  description: "",
  always_include: false,
};

/**
 * Writes a Memory Item count like "· 97 items".
 *
 * @param count - How many Memory Items there are.
 * @returns The count with the right word.
 */
function itemCountLabel(count: number): string {
  return `· ${count} ${count === 1 ? "item" : "items"}`;
}

/**
 * The admin Memory Categories manager: active categories with their
 * "always include" switch and Archive, archived ones with Restore, and a form
 * to add a category or change its name and description. There is no delete.
 *
 * @returns The lists and form, or a loading, empty or error state.
 */
export function MemoryCategoriesManager() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [editing, setEditing] = useState<Editing | null>(null);
  const [flash, setFlash] = useState<Flash | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setState({
        kind: "loaded",
        categories: await apiClient.listMemoryCategories(),
      });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runRowAction(
    category: MemoryCategoryOverview,
    action: () => Promise<unknown>,
    successText: string | null,
  ) {
    setBusyId(category.id);
    setFlash(null);
    try {
      await action();
      if (successText) {
        setFlash({ text: successText, isError: false });
      }
      await load();
    } catch (error) {
      setFlash({
        text:
          error instanceof ApiError && error.status === 409 && error.detail
            ? error.detail
            : `Couldn’t change ${category.name}. Please try again.`,
        isError: true,
      });
    } finally {
      setBusyId(null);
    }
  }

  function startEditing(next: Editing) {
    setEditing(next);
    setFlash(null);
  }

  async function saveForm(input: MemoryCategoryInput) {
    if (editing?.kind === "edit") {
      await apiClient.updateMemoryCategory(editing.category.id, input);
      setFlash({ text: `Saved ${input.name.trim()}.`, isError: false });
    } else {
      await apiClient.addMemoryCategory(input);
      setFlash({ text: `Added ${input.name.trim()}.`, isError: false });
    }
    setEditing(null);
    await load();
  }

  const header = (
    <>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p
          role="note"
          className="m-0 max-w-[48em] flex-1 rounded-xl bg-yellow-tint px-4 py-3.5 text-sm text-yellow-deep"
        >
          Categories can’t be deleted, because existing Memory Items belong to
          them. Archive instead: Zeph stops saving new memories there, and Users
          still see and can delete the ones they have.
        </p>
        <button
          type="button"
          className={primaryButton}
          onClick={() => startEditing({ kind: "add" })}
        >
          Add category
        </button>
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
        <MemoryCategoryForm
          key={editing.kind === "edit" ? editing.category.id : "add"}
          title={
            editing.kind === "edit"
              ? `Edit ${editing.category.name}`
              : "New category"
          }
          initial={editing.kind === "edit" ? editing.category : emptyCategory}
          onSubmit={saveForm}
          onCancel={() => setEditing(null)}
        />
      ) : null}
    </>
  );

  if (state.kind === "loading") {
    return (
      <div className="flex flex-col gap-[30px]">
        {header}
        <div
          aria-busy="true"
          aria-label="Loading categories"
          className="h-[320px] rounded-card border border-line bg-subtle"
        />
      </div>
    );
  }

  if (state.kind === "failed") {
    return (
      <div className="flex flex-col gap-[30px]">
        {header}
        <LoadFailed
          title="Couldn’t load Memory Categories"
          body="Zeph keeps using the last saved set."
          onRetry={() => void load()}
        />
      </div>
    );
  }

  const active = state.categories.filter((category) => !category.archived);
  const archived = state.categories.filter((category) => category.archived);

  if (state.categories.length === 0) {
    return (
      <div className="flex flex-col gap-[30px]">
        {header}
        <div className="flex flex-col gap-1 rounded-xl border border-dashed border-line-strong px-5 py-6">
          <span className="font-semibold">No categories yet</span>
          <p className="m-0 max-w-[34em] text-caption text-ink-muted">
            Zeph needs at least one active category to save memories. Suggested
            starters: Life details, Relationships, Goals, Values & beliefs,
            Challenges, Preferences, What helps.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-[30px]">
      {header}

      <section
        aria-labelledby="active-categories-heading"
        className="flex flex-col rounded-card border border-line bg-white"
      >
        <h2
          id="active-categories-heading"
          className="m-0 px-5 pb-2 pt-4 text-[17px] font-semibold"
        >
          Active{" "}
          <span className="text-caption font-normal text-ink-muted">
            {active.length}
          </span>
        </h2>
        <ul className="m-0 list-none p-0">
          {active.map((category) => {
            const isBusy = busyId === category.id;
            return (
              <li
                key={category.id}
                className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3"
              >
                <span className="flex min-w-0 flex-[1_1_280px] flex-col">
                  <span>
                    <span className="font-semibold">{category.name}</span>{" "}
                    <span className="text-caption text-ink-muted">
                      {itemCountLabel(category.item_count)}
                    </span>
                  </span>
                  <span className="text-caption text-ink-soft">
                    {category.description}
                  </span>
                </span>
                <span className="flex flex-wrap items-center gap-2.5">
                  <span className="inline-flex items-center gap-2 text-[13px]">
                    Always include
                    <Switch
                      label={`Always include ${category.name}`}
                      checked={category.always_include}
                      disabled={isBusy}
                      onChange={(checked) =>
                        void runRowAction(
                          category,
                          () =>
                            apiClient.updateMemoryCategory(category.id, {
                              name: category.name,
                              description: category.description,
                              always_include: checked,
                            }),
                          null,
                        )
                      }
                    />
                  </span>
                  <button
                    type="button"
                    className={compactSecondaryButton}
                    disabled={isBusy}
                    onClick={() => startEditing({ kind: "edit", category })}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className={compactSecondaryButton}
                    disabled={isBusy}
                    onClick={() =>
                      void runRowAction(
                        category,
                        () => apiClient.archiveMemoryCategory(category.id),
                        `Archived ${category.name}. Its memories are kept.`,
                      )
                    }
                  >
                    Archive
                  </button>
                </span>
              </li>
            );
          })}
        </ul>
        <p className="m-0 border-t border-line px-5 py-3 text-caption text-ink-muted">
          “Always include” sends every memory in that category to Zeph on each
          reply, not just the most relevant ones. Use sparingly.
        </p>
      </section>

      <section
        aria-labelledby="archived-categories-heading"
        className="flex flex-col rounded-card border border-line"
      >
        <h2
          id="archived-categories-heading"
          className="m-0 px-5 pb-2 pt-4 text-[17px] font-semibold text-ink-soft"
        >
          Archived{" "}
          <span className="text-caption font-normal text-ink-muted">
            {archived.length}
          </span>
        </h2>
        {archived.length === 0 ? (
          <p className="m-0 px-5 pb-4 text-caption text-ink-muted">
            Nothing archived.
          </p>
        ) : (
          <ul className="m-0 list-none p-0">
            {archived.map((category) => (
              <li
                key={category.id}
                className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3"
              >
                <span className="flex min-w-0 flex-[1_1_280px] flex-col">
                  <span>
                    <span className="font-semibold text-ink-soft">
                      {category.name}
                    </span>{" "}
                    <span className="text-caption text-ink-muted">
                      {itemCountLabel(category.item_count)} kept
                    </span>
                  </span>
                  <span className="text-caption text-ink-muted">
                    {category.description}
                  </span>
                </span>
                <button
                  type="button"
                  className={compactSecondaryButton}
                  disabled={busyId === category.id}
                  onClick={() =>
                    void runRowAction(
                      category,
                      () => apiClient.restoreMemoryCategory(category.id),
                      `Restored ${category.name}.`,
                    )
                  }
                >
                  Restore
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
