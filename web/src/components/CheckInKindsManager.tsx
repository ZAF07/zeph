"use client";

import { useCallback, useEffect, useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { CheckInKindCard } from "@/components/CheckInKindCard";
import { LoadFailed } from "@/components/LoadFailed";
import type { CheckInKindInput, CheckInKindOverview } from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; kinds: CheckInKindOverview[] };

const emptyKind: CheckInKindInput = {
  name: "",
  description: "",
  allowed_without_user_memory: false,
};

/**
 * The admin Check-in Kinds manager: a card per Kind to edit its name,
 * description and "allowed when memory is off", or remove it, and a card to
 * add a new one.
 *
 * @returns The cards, or a loading, empty or error state.
 */
export function CheckInKindsManager() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [isAdding, setIsAdding] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setState({ kind: "loaded", kinds: await apiClient.listCheckInKinds() });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  async function add(input: CheckInKindInput) {
    await apiClient.addCheckInKind(input);
    setIsAdding(false);
    setFlash(`Added ${input.name.trim()}.`);
    await load();
  }

  async function save(kind: CheckInKindOverview, input: CheckInKindInput) {
    await apiClient.updateCheckInKind(kind.id, input);
    setFlash(`Saved ${input.name.trim()}.`);
    await load();
  }

  async function remove(kind: CheckInKindOverview) {
    await apiClient.removeCheckInKind(kind.id);
    setFlash(`Removed ${kind.name}.`);
    await load();
  }

  const addButton = (
    <button
      type="button"
      className={`${primaryButton} self-start`}
      disabled={isAdding}
      onClick={() => {
        setIsAdding(true);
        setFlash(null);
      }}
    >
      Add Check-in Kind
    </button>
  );

  if (state.kind === "loading") {
    return (
      <div
        aria-busy="true"
        aria-label="Loading Check-in Kinds"
        className="grid gap-4 sm:grid-cols-2"
      >
        <span className="block h-[220px] rounded-card bg-subtle" />
        <span className="block h-[220px] rounded-card bg-subtle" />
      </div>
    );
  }

  if (state.kind === "failed") {
    return (
      <LoadFailed
        title="Couldn’t load Check-in Kinds"
        body="Check-ins keep running with the last saved set."
        onRetry={() => void load()}
      />
    );
  }

  return (
    <div className="flex flex-col gap-[30px]">
      {addButton}

      {flash ? (
        <p
          role="status"
          className="m-0 rounded-xl bg-blue-tint px-4 py-3.5 text-sm text-blue-deep"
        >
          {flash}
        </p>
      ) : null}

      {state.kinds.length === 0 && !isAdding ? (
        <div className="flex flex-col items-center gap-1 rounded-card border border-dashed border-line-strong px-6 py-8 text-center">
          <span className="text-h3">No Check-in Kinds</span>
          <p className="m-0 max-w-[34em] text-caption text-ink-muted">
            Without at least one, Zeph won’t start any Check-ins — it will only
            reply. Add a casual hello to begin.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(min(420px,100%),1fr))] gap-4">
          {state.kinds.map((kind) => (
            <CheckInKindCard
              key={kind.id}
              initial={kind}
              isNew={false}
              sentLast30Days={kind.sent_last_30_days}
              sendsSharedPhoto={kind.sends_shared_photo}
              onSave={(input) => save(kind, input)}
              onRemove={() => remove(kind)}
            />
          ))}
          {isAdding ? (
            <CheckInKindCard
              initial={emptyKind}
              isNew
              sentLast30Days={0}
              onSave={add}
              onCancel={() => setIsAdding(false)}
            />
          ) : null}
        </div>
      )}
    </div>
  );
}
