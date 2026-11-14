"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import { LoadFailed } from "@/components/LoadFailed";
import { PersonalStickerPicture } from "@/components/PersonalStickerPicture";
import type { PersonalSticker } from "@/lib/api-client";
import { notAvailableText } from "@/lib/features";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Your stickers section: each sticker Zeph kept from the User, with its
 * image and when Zeph uses it, each removable. It stays visible when
 * Personal Stickers isn't available, so the User can still see and remove
 * what was kept.
 *
 * @param props - `available` is false when Personal Stickers doesn't work
 *   for the User.
 * @returns The section.
 */
export function PersonalStickersSection({ available }: { available: boolean }) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const stickersQuery = useQuery({
    queryKey: queryKeys.personalStickers,
    queryFn: () => apiClient.listPersonalStickers(),
  });
  const stickers = stickersQuery.data;

  const removeSticker = useMutation({
    mutationFn: (stickerId: string) =>
      apiClient.deletePersonalSticker(stickerId),
    onSuccess: (_, stickerId) =>
      queryClient.setQueryData<PersonalSticker[]>(
        queryKeys.personalStickers,
        (current) => current?.filter((sticker) => sticker.id !== stickerId),
      ),
  });

  return (
    <section
      aria-labelledby="personal-stickers-heading"
      className="flex flex-col gap-4 rounded-card border border-line bg-white p-8"
    >
      <h2
        id="personal-stickers-heading"
        className="m-0 text-[17px] font-semibold"
      >
        Your stickers
      </h2>
      {available ? null : (
        <p className="m-0 text-sm font-medium text-ink-soft">
          {notAvailableText}
        </p>
      )}
      <p className="m-0 text-[15px] text-ink-soft">
        Stickers you sent that Zeph kept, so it can now and then reply in your
        own stickers, with when it uses each. Remove any you’d rather it didn’t
        use.
      </p>

      {removeSticker.isError ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          We couldn’t remove that. Please try again.
        </p>
      ) : null}

      {stickersQuery.isPending ? (
        <span
          aria-busy="true"
          aria-label="Loading your stickers"
          className="block h-[96px] rounded-card bg-subtle"
        />
      ) : null}

      {!stickers && stickersQuery.isError ? (
        <LoadFailed
          title="We couldn’t load your stickers"
          body="Nothing has been removed."
          onRetry={() => void stickersQuery.refetch()}
        />
      ) : null}

      {stickers && stickers.length > 0 ? (
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {stickers.map((sticker) => {
            const name = sticker.emoji ?? "with no emoji";
            return (
              <li
                key={sticker.id}
                className="flex items-center gap-4 rounded-card border border-line p-3"
              >
                <PersonalStickerPicture sticker={sticker} />
                <span className="min-w-0 flex-auto text-[15px]">
                  {sticker.note}
                </span>
                <button
                  type="button"
                  aria-label={`Remove sticker ${name}`}
                  className={deleteIconButton}
                  disabled={removeSticker.isPending}
                  onClick={() => removeSticker.mutate(sticker.id)}
                >
                  <DeleteIcon />
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}

      {stickers && stickers.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-10 text-center">
          <span className="text-[17px] font-medium">No stickers kept yet</span>
          <p className="m-0 text-caption text-ink-muted">
            When you send Zeph a sticker whose meaning is clear, it may keep it
            here after the Conversation ends.
          </p>
        </div>
      ) : null}
    </section>
  );
}
