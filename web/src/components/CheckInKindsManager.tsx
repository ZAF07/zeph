"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { CardCount } from "@/components/CardCount";
import { CardListLoading } from "@/components/CardListLoading";
import { CardList } from "@/components/CardList";
import { CheckInKindCard } from "@/components/CheckInKindCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadFailed } from "@/components/LoadFailed";
import { NewCheckInKindBox } from "@/components/NewCheckInKindBox";
import { SavedNote } from "@/components/SavedNote";
import type { CheckInKindInput, CheckInKindOverview } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Check-in Kinds manager, the card-list template: the count,
 * Expand all, Collapse all and Add, then a folding card per Kind to edit
 * its name and description or remove it. A new Kind is added in a box
 * above the list.
 *
 * @returns The list, or a loading, empty or error state.
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

  function startAdding() {
    setIsAdding(true);
    setFlash(null);
  }

  if (!kinds) {
    if (kindsQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Check-in Kinds"
          body="Check your connection and try again."
          onRetry={() => void kindsQuery.refetch()}
        />
      );
    }
    return <CardListLoading label="Loading Check-in Kinds" />;
  }

  return (
    <CardList
      items={kinds}
      count={
        <CardCount
          count={kinds.length}
          words={kinds.length === 1 ? "kind" : "kinds"}
        />
      }
      addLabel="Add a Check-in Kind"
      onAdd={startAdding}
      isAddDisabled={isAdding}
      aboveList={
        <>
          {flash ? <SavedNote>{flash}</SavedNote> : null}
          {isAdding ? (
            <NewCheckInKindBox
              onAdd={add}
              onCancel={() => setIsAdding(false)}
            />
          ) : null}
          {kinds.length === 0 && !isAdding ? (
            <EmptyState
              title="No Check-in Kinds"
              body="Without a kind, Zeph can’t start a check-in. Add one to begin."
              action={
                <button
                  type="button"
                  className={secondaryButton}
                  onClick={startAdding}
                >
                  Add a Check-in Kind
                </button>
              }
            />
          ) : null}
        </>
      }
      renderCard={(kind, _index, folding) => (
        <CheckInKindCard
          key={kind.id}
          kind={kind}
          isOpen={folding.isOpen}
          onToggle={folding.onToggle}
          onSave={(input) => save(kind, input)}
          onRemove={() => remove(kind)}
        />
      )}
    />
  );
}
