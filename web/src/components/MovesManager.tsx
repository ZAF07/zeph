"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { primaryButton } from "@/components/button-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { MoveCard } from "@/components/MoveCard";
import type { Move, MoveDirection, MoveInput } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

type Flash = { text: string; isError: boolean };

const emptyMove: MoveInput = {
  name: "",
  when_it_fits: "",
  how_to_do_it: "",
  needed_feature: null,
};

/**
 * The admin Moves manager: a card per Move, in order, to edit, move or
 * remove it and choose the Feature it needs, and a card to add a new one.
 *
 * @returns The cards, or a loading or error state.
 */
export function MovesManager() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [flash, setFlash] = useState<Flash | null>(null);
  const movesQuery = useQuery({
    queryKey: queryKeys.moves,
    queryFn: () => apiClient.listMoves(),
  });
  const featuresQuery = useQuery({
    queryKey: queryKeys.features,
    queryFn: () => apiClient.listFeatures(),
  });
  const moveMutation = useMutation({
    mutationFn: ({
      move,
      direction,
    }: {
      move: Move;
      direction: MoveDirection;
    }) => apiClient.moveMove(move.id, direction),
    onMutate: () => setFlash(null),
    onSuccess: (moves) => queryClient.setQueryData(queryKeys.moves, moves),
    onError: (_, { move }) =>
      setFlash({
        text: `Couldn’t move ${move.name}. Please try again.`,
        isError: true,
      }),
  });
  const moves = movesQuery.data;
  const features = featuresQuery.data;

  async function reloadMoves() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.moves });
    await queryClient.invalidateQueries({ queryKey: queryKeys.needs });
  }

  async function add(input: MoveInput) {
    await apiClient.addMove(input);
    setIsAdding(false);
    setFlash({ text: `Added ${input.name.trim()}.`, isError: false });
    await reloadMoves();
  }

  async function save(move: Move, input: MoveInput) {
    await apiClient.updateMove(move.id, input);
    setFlash({ text: `Saved ${input.name.trim()}.`, isError: false });
    await reloadMoves();
  }

  async function remove(move: Move) {
    await apiClient.deleteMove(move.id);
    setFlash({ text: `Removed ${move.name}.`, isError: false });
    await reloadMoves();
  }

  if (!moves || !features) {
    if (movesQuery.isError || featuresQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Moves"
          body="Zeph keeps using the last saved Moves."
          onRetry={() => {
            void movesQuery.refetch();
            void featuresQuery.refetch();
          }}
        />
      );
    }
    return (
      <div
        aria-busy="true"
        aria-label="Loading Moves"
        className="flex flex-col gap-4"
      >
        <span className="block h-[300px] rounded-card bg-subtle" />
        <span className="block h-[300px] rounded-card bg-subtle" />
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
        Add Move
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
        {moves.map((move, index) => (
          <MoveCard
            key={move.id}
            initial={move}
            isNew={false}
            features={features}
            onSave={(input) => save(move, input)}
            onRemove={() => remove(move)}
            onMove={(direction) => moveMutation.mutate({ move, direction })}
            canMoveUp={index > 0}
            canMoveDown={index < moves.length - 1}
            isMoving={moveMutation.isPending}
          />
        ))}
        {isAdding ? (
          <MoveCard
            initial={emptyMove}
            isNew
            features={features}
            onSave={add}
            onCancel={() => setIsAdding(false)}
          />
        ) : null}
      </div>
    </div>
  );
}
