"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { CheckInKindCard } from "@/components/CheckInKindCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadFailed } from "@/components/LoadFailed";
import { SavedNote } from "@/components/SavedNote";
import type { CheckInKindInput, CheckInKindOverview } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const emptyKind: CheckInKindInput = { name: "", description: "" };

/**
 * The admin Check-in Kinds manager: a card per Kind to edit its name and
 * description, or remove it, and a card to add a new one.
 *
 * @returns The cards, or a loading, empty or error state.
 */
export function CheckInKindsManager() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [flash, setFlash] = useState<string | null>(null);
  const kindsQuery = useQuery({
    queryKey: queryKeys.checkInKinds,
    queryFn: () => apiClient.listCheckInKinds(),
  });
  const kinds = kindsQuery.data;

  async function reloadKinds() {
    void queryClient.invalidateQueries({ queryKey: queryKeys.checkIns });
    await queryClient.invalidateQueries({ queryKey: queryKeys.checkInKinds });
  }

  async function add(input: CheckInKindInput) {
    await apiClient.addCheckInKind(input);
    setIsAdding(false);
    setFlash(`Added ${input.name.trim()}.`);
    await reloadKinds();
  }

  async function save(kind: CheckInKindOverview, input: CheckInKindInput) {
    await apiClient.updateCheckInKind(kind.id, input);
    setFlash(`Saved ${input.name.trim()}.`);
    await reloadKinds();
  }

  async function remove(kind: CheckInKindOverview) {
    await apiClient.removeCheckInKind(kind.id);
    setFlash(`Removed ${kind.name}.`);
    await reloadKinds();
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

  if (!kinds) {
    if (kindsQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Check-in Kinds"
          body="Check-ins keep running with the last saved set."
          onRetry={() => void kindsQuery.refetch()}
        />
      );
    }
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

  return (
    <div className="flex flex-col gap-[30px]">
      {addButton}

      {flash ? <SavedNote>{flash}</SavedNote> : null}

      {kinds.length === 0 && !isAdding ? (
        <EmptyState
          title="No Check-in Kinds"
          body="Without at least one, Zeph won’t start any Check-ins — it will only reply. Add a casual hello to begin."
        />
      ) : (
        <div className="grid grid-cols-[repeat(auto-fit,minmax(min(420px,100%),1fr))] gap-4">
          {kinds.map((kind) => (
            <CheckInKindCard
              key={kind.id}
              initial={kind}
              isNew={false}
              sentLast30Days={kind.sent_last_30_days}
              sendsSharedPhoto={kind.sends_shared_photo}
              raisesCuriosity={kind.raises_curiosity}
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
