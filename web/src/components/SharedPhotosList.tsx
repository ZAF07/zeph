"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import { EmptyState } from "@/components/EmptyState";
import { MemoriesPanelHeading } from "@/components/MemoriesPanelHeading";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { SharedPhotoPicture } from "@/components/SharedPhotoPicture";
import type { SharedPhoto } from "@/lib/api-client";
import { type Copy, fillCopy, readCopy } from "@/lib/copy";
import { formatShortDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Photos tab: each Shared Photo, newest first, with its photo,
 * description, why it matters and the day it was sent; each can be deleted
 * but not edited.
 *
 * @param props - `photos` are the User's Shared Photos, newest first,
 *   `copy` is the Memories page's Copy, and `timeZone` is the User's time
 *   zone.
 * @returns The tab's content.
 */
export function SharedPhotosList({
  photos,
  copy,
  timeZone,
}: {
  photos: SharedPhoto[];
  copy: Copy;
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  const deletePhoto = useMutation({
    mutationFn: (photoId: string) => apiClient.deleteSharedPhoto(photoId),
    onSuccess: (_, photoId) =>
      queryClient.setQueryData(
        queryKeys.sharedPhotos,
        photos.filter((item) => item.id !== photoId),
      ),
  });

  return (
    <>
      <MemoriesPanelHeading
        title={readCopy(copy, "memories.photos.heading")}
        body={readCopy(copy, "memories.photos.lead")}
      />

      {deletePhoto.isError ? (
        <SaveFailedNote>
          {readCopy(copy, "memories.delete_failed")}
        </SaveFailedNote>
      ) : null}

      {photos.length > 0 ? (
        <ol className="m-0 flex list-none flex-col gap-6 p-0">
          {photos.map((photo) => {
            const day = formatShortDay(photo.sent_at, timeZone);
            const withDay = (slot: string) => fillCopy(copy, slot, { day });
            return (
              <li
                key={photo.id}
                className="box-border rounded-card border border-line bg-panel py-[18px] pr-3 pl-[22px] [overflow-wrap:anywhere]"
              >
                <div className="flex flex-wrap items-start gap-x-5 gap-y-4">
                  <SharedPhotoPicture
                    photo={photo}
                    label={withDay("memories.photos.photo_label")}
                    loadingText={readCopy(
                      copy,
                      "memories.photos.photo_loading",
                    )}
                    failedText={readCopy(copy, "memories.photos.photo_failed")}
                  />
                  <div className="flex min-w-0 flex-[1_1_260px] flex-col gap-1.5">
                    <p className="m-0 text-[15px] text-text">
                      {photo.description}
                    </p>
                    <p className="m-0 text-[14px] text-soft">{photo.note}</p>
                    <span className="text-[12px] text-soft">
                      {withDay("memories.photos.sent")}
                    </span>
                  </div>
                  <button
                    type="button"
                    aria-label={withDay("memories.photos.delete")}
                    className={deleteIconButton}
                    disabled={deletePhoto.isPending}
                    onClick={() => deletePhoto.mutate(photo.id)}
                  >
                    <DeleteIcon />
                  </button>
                </div>
              </li>
            );
          })}
        </ol>
      ) : (
        <EmptyState
          title={readCopy(copy, "memories.photos.empty_title")}
          body={readCopy(copy, "memories.photos.empty_body")}
        />
      )}
    </>
  );
}
