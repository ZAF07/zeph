"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { LoadFailed } from "@/components/LoadFailed";
import { StickerAddPanel } from "@/components/StickerAddPanel";
import { StickerCard } from "@/components/StickerCard";
import type { Sticker } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * Writes a sticker count like "6 stickers".
 *
 * @param count - How many stickers there are.
 * @returns The count with the right word.
 */
function stickerCountLabel(count: number): string {
  return `${count} ${count === 1 ? "sticker" : "stickers"}`;
}

/**
 * The admin Sticker Library: the "Add stickers" card, then every sticker
 * with its "when to use" note and Remove.
 *
 * @returns The library, or a loading, empty or error state.
 */
export function StickerLibrary() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const stickersQuery = useQuery({
    queryKey: queryKeys.stickers,
    queryFn: () => apiClient.listStickers(),
  });
  const stickers = stickersQuery.data;

  async function reloadStickers() {
    await queryClient.invalidateQueries({ queryKey: queryKeys.stickers });
  }

  async function remove(sticker: Sticker) {
    await apiClient.removeSticker(sticker.id);
    await reloadStickers();
  }

  return (
    <div className="flex flex-col gap-[30px]">
      <StickerAddPanel onAdded={() => void reloadStickers()} />

      {stickersQuery.isPending ? (
        <div
          aria-busy="true"
          aria-label="Loading stickers"
          className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-3"
        >
          {[1, 2, 3, 4].map((placeholder) => (
            <span
              key={placeholder}
              className="h-60 rounded-2xl border border-line bg-subtle"
            />
          ))}
        </div>
      ) : null}

      {!stickers && stickersQuery.isError ? (
        <LoadFailed
          title="Couldn’t load stickers"
          body="Zeph keeps sending stickers from the last saved library."
          onRetry={() => void stickersQuery.refetch()}
        />
      ) : null}

      {stickers && stickers.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            No stickers yet
          </span>
          <p className="m-0 text-caption text-ink-muted">
            Zeph replies in words only until you add some.
          </p>
        </div>
      ) : null}

      {stickers && stickers.length > 0 ? (
        <>
          <p className="m-0 text-caption text-ink-muted">
            {stickerCountLabel(stickers.length)}
          </p>
          <ul className="m-0 grid list-none grid-cols-[repeat(auto-fill,minmax(min(200px,100%),1fr))] gap-3 p-0">
            {stickers.map((sticker) => (
              <StickerCard
                key={sticker.id}
                sticker={sticker}
                onRemove={() => remove(sticker)}
              />
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}
