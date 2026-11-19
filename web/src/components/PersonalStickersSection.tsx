"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import { EmptyState } from "@/components/EmptyState";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { PersonalStickerPicture } from "@/components/PersonalStickerPicture";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { PersonalSticker } from "@/lib/api-client";
import { type Copy, fillCopy, readCopy } from "@/lib/copy";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Your stickers section: each sticker Zeph kept from the User, with its
 * image and when Zeph uses it, each removable. It stays visible when
 * Personal Stickers isn't available, so the User can still see and remove
 * what was kept.
 *
 * @param props - `available` is false when Personal Stickers doesn't work
 *   for the User; `copy` holds the Account page's Copy.
 * @returns The section.
 */
export function PersonalStickersSection({
  available,
  copy,
}: {
  available: boolean;
  copy: Copy;
}) {
  const accountCopy = (slot: string) => readCopy(copy, `account.${slot}`);
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
      className="flex flex-col gap-5 min-[900px]:gap-6"
    >
      <div>
        <h2
          id="personal-stickers-heading"
          className="m-0 text-[20px] font-normal text-cream"
        >
          {accountCopy("stickers.heading")}
        </h2>
        {available ? null : (
          <p className="mt-1.5 mb-0 max-w-[600px] text-[14px] text-soft">
            {accountCopy("not_available")}
          </p>
        )}
        <p className="mt-1.5 mb-0 max-w-[600px] text-[14px] text-soft">
          {accountCopy("stickers.lead")}
        </p>
      </div>

      {removeSticker.isError ? (
        <SaveFailedNote>{accountCopy("stickers.remove_failed")}</SaveFailedNote>
      ) : null}

      {stickersQuery.isPending ? (
        <LoadingPanel shape="card" label={accountCopy("stickers.loading")} />
      ) : null}

      {!stickers && stickersQuery.isError ? (
        <LoadFailed
          title={accountCopy("stickers.load_failed_title")}
          body={accountCopy("stickers.load_failed_body")}
          retryLabel={accountCopy("load_failed.retry")}
          onRetry={() => void stickersQuery.refetch()}
        />
      ) : null}

      {stickers && stickers.length > 0 ? (
        <ul className="m-0 flex list-none flex-wrap gap-3 p-0">
          {stickers.map((sticker) => (
            <li
              key={sticker.id}
              className="flex min-w-0 flex-[1_1_200px] items-center gap-3 rounded-tile border border-line py-2.5 pr-1.5 pl-3"
            >
              <PersonalStickerPicture sticker={sticker} copy={copy} />
              <span className="min-w-0 flex-1 text-[13px] text-soft">
                {sticker.note}
              </span>
              <button
                type="button"
                aria-label={
                  sticker.emoji
                    ? fillCopy(copy, "account.stickers.remove", {
                        emoji: sticker.emoji,
                      })
                    : accountCopy("stickers.remove_no_emoji")
                }
                className={deleteIconButton}
                disabled={removeSticker.isPending}
                onClick={() => removeSticker.mutate(sticker.id)}
              >
                <DeleteIcon />
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {stickers && stickers.length === 0 ? (
        <EmptyState
          title={accountCopy("stickers.empty_title")}
          body={accountCopy("stickers.empty_body")}
        />
      ) : null}
    </section>
  );
}
