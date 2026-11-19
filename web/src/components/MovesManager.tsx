"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { CardCount } from "@/components/CardCount";
import { CardList } from "@/components/CardList";
import { CardListFlash, type Flash } from "@/components/CardListFlash";
import { CardListLoading } from "@/components/CardListLoading";
import { LoadFailed } from "@/components/LoadFailed";
import { MoveCard } from "@/components/MoveCard";
import { NewMoveBox } from "@/components/NewMoveBox";
import type { Move, MoveDirection, MoveInput } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Moves manager, from the card-list template: a folding card per
 * Move, in order, to edit, move or remove it and choose the Feature it
 * needs, and a box above the list to add one.
 *
 * @returns The list, or a loading or error state.
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

  async function reloadMovesAndNeeds() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.moves });
    await queryClient.invalidateQueries({ queryKey: queryKeys.needs });
  }

  async function add(input: MoveInput) {
    await apiClient.addMove(input);
    setIsAdding(false);
    setFlash({ text: `Added ${input.name.trim()}.`, isError: false });
    await reloadMovesAndNeeds();
  }

  async function save(move: Move, input: MoveInput) {
    await apiClient.updateMove(move.id, input);
    setFlash({ text: `Saved ${input.name.trim()}.`, isError: false });
    await reloadMovesAndNeeds();
  }

  async function remove(move: Move) {
    await apiClient.deleteMove(move.id);
    setFlash({ text: `Removed ${move.name}.`, isError: false });
    await reloadMovesAndNeeds();
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
    return <CardListLoading label="Loading Moves" />;
  }

  return (
    <CardList
      items={moves}
      count={
        <CardCount
          count={moves.length}
          words={moves.length === 1 ? "Move" : "Moves"}
        />
      }
      addLabel="Add Move"
      onAdd={() => {
        setIsAdding(true);
        setFlash(null);
      }}
      isAddDisabled={isAdding}
      aboveList={
        <>
          <CardListFlash flash={flash} />
          {isAdding ? (
            <NewMoveBox
              features={features}
              onAdd={add}
              onCancel={() => setIsAdding(false)}
            />
          ) : null}
        </>
      }
      renderCard={(move, index, folding) => (
        <MoveCard
          key={move.id}
          move={move}
          features={features}
          isOpen={folding.isOpen}
          onToggle={folding.onToggle}
          onSave={(input) => save(move, input)}
          onRemove={() => remove(move)}
          onMove={(direction) => moveMutation.mutate({ move, direction })}
          canMoveUp={index > 0}
          canMoveDown={index < moves.length - 1}
          isMoving={moveMutation.isPending}
        />
      )}
    />
  );
}
