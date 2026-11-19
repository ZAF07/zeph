"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { CardCount } from "@/components/CardCount";
import { CardList } from "@/components/CardList";
import { CardListFlash, type Flash } from "@/components/CardListFlash";
import { CardListLoading } from "@/components/CardListLoading";
import { EmptyState } from "@/components/EmptyState";
import { LoadFailed } from "@/components/LoadFailed";
import { StickerAddBox } from "@/components/StickerAddBox";
import { StickerCard } from "@/components/StickerCard";
import type { Sticker } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Sticker Library, from the card-list template: a folding card
 * per sticker with its "when to use" note and Remove, and the "Add
 * stickers" box above the list.
 *
 * @returns The library, or a loading, empty or error state.
 */
export function StickerLibrary() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [flash, setFlash] = useState<Flash | null>(null);
  const stickersQuery = useQuery({
    queryKey: queryKeys.stickers,
    queryFn: () => apiClient.listStickers(),
  });
  const stickers = stickersQuery.data;

  async function reloadStickers() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.stickers });
  }

  async function saveNote(sticker: Sticker, note: string) {
    await apiClient.saveStickerNote(sticker.id, note);
    setFlash({ text: "Saved the note.", isError: false });
    await reloadStickers();
  }

  async function remove(sticker: Sticker) {
    await apiClient.removeSticker(sticker.id);
    setFlash({ text: "Removed the sticker.", isError: false });
    await reloadStickers();
  }

  if (!stickers) {
    if (stickersQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load stickers"
          body="Zeph keeps sending stickers from the last saved library."
          onRetry={() => void stickersQuery.refetch()}
        />
      );
    }
    return <CardListLoading label="Loading stickers" />;
  }

  return (
    <CardList
      items={stickers}
      count={
        <CardCount
          count={stickers.length}
          words={stickers.length === 1 ? "sticker" : "stickers"}
        />
      }
      addLabel="Add stickers"
      onAdd={() => {
        setIsAdding(true);
        setFlash(null);
      }}
      isAddDisabled={isAdding}
      aboveList={
        <>
          <CardListFlash flash={flash} />
          {isAdding ? (
            <StickerAddBox
              onAdded={() => void reloadStickers()}
              onClose={() => setIsAdding(false)}
            />
          ) : null}
          {stickers.length === 0 ? (
            <EmptyState
              title="No stickers yet"
              body="Zeph replies in words only until you add some."
            />
          ) : null}
        </>
      }
      renderCard={(sticker, _index, folding) => (
        <StickerCard
          key={sticker.id}
          sticker={sticker}
          isOpen={folding.isOpen}
          onToggle={folding.onToggle}
          onSaveNote={(note) => saveNote(sticker, note)}
          onRemove={() => remove(sticker)}
        />
      )}
    />
  );
}
