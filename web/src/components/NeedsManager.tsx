"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { NeedCard } from "@/components/NeedCard";
import type { MoveDirection, Need, NeedInput } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

type Flash = { text: string; isError: boolean };

const emptyNeed: NeedInput = { name: "", when_it_fits: "", how_to_reply: "" };

/**
 * The admin Needs manager: a card per Need, in order, to edit, move or
 * remove it, and a card to add a new one. The fallback Need can't be
 * removed.
 *
 * @returns The cards, or a loading or error state.
 */
export function NeedsManager() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [flash, setFlash] = useState<Flash | null>(null);
  const needsQuery = useQuery({
    queryKey: queryKeys.needs,
    queryFn: () => apiClient.listNeeds(),
  });
  const moveMutation = useMutation({
    mutationFn: ({
      need,
      direction,
    }: {
      need: Need;
      direction: MoveDirection;
    }) => apiClient.moveNeed(need.id, direction),
    onMutate: () => setFlash(null),
    onSuccess: (needs) => queryClient.setQueryData(queryKeys.needs, needs),
    onError: (_, { need }) =>
      setFlash({
        text: `Couldn’t move ${need.name}. Please try again.`,
        isError: true,
      }),
  });
  const needs = needsQuery.data;

  async function reloadNeeds() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.needs });
  }

  async function add(input: NeedInput) {
    await apiClient.addNeed(input);
    setIsAdding(false);
    setFlash({ text: `Added ${input.name.trim()}.`, isError: false });
    await reloadNeeds();
  }

  async function save(need: Need, input: NeedInput) {
    await apiClient.updateNeed(need.id, input);
    setFlash({ text: `Saved ${input.name.trim()}.`, isError: false });
    await reloadNeeds();
  }

  async function remove(need: Need) {
    await apiClient.deleteNeed(need.id);
    setFlash({ text: `Removed ${need.name}.`, isError: false });
    await reloadNeeds();
  }

  if (!needs) {
    if (needsQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Needs"
          body="Zeph keeps using the last saved Needs."
          onRetry={() => void needsQuery.refetch()}
        />
      );
    }
    return (
      <div
        aria-busy="true"
        aria-label="Loading Needs"
        className="flex flex-col gap-4"
      >
        <span className="block h-[260px] rounded-card bg-subtle" />
        <span className="block h-[260px] rounded-card bg-subtle" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-[30px]">
      <button
        type="button"
        className={`${primaryButton} self-start`}
        disabled={isAdding}
        onClick={() => {
          setIsAdding(true);
          setFlash(null);
        }}
      >
        Add Need
      </button>

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

      <div className="flex flex-col gap-4">
        {needs.map((need, index) => (
          <NeedCard
            key={need.id}
            initial={need}
            isNew={false}
            isFallback={need.is_fallback}
            onSave={(input) => save(need, input)}
            onRemove={need.is_fallback ? undefined : () => remove(need)}
            onMove={(direction) => moveMutation.mutate({ need, direction })}
            canMoveUp={index > 0}
            canMoveDown={index < needs.length - 1}
            isMoving={moveMutation.isPending}
          />
        ))}
        {isAdding ? (
          <NeedCard
            initial={emptyNeed}
            isNew
            onSave={add}
            onCancel={() => setIsAdding(false)}
          />
        ) : null}
      </div>
    </div>
  );
}
