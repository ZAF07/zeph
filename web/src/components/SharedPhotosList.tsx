"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { deleteIconButton } from "@/components/button-styles";
import { DeleteIcon } from "@/components/DeleteIcon";
import { SharedPhotoPicture } from "@/components/SharedPhotoPicture";
import type { SharedPhoto } from "@/lib/api-client";
import { formatWeekdayDay } from "@/lib/dates";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Photos tab: each Shared Photo, newest first, with its photo,
 * description, why it matters and the day it was sent; each can be deleted
 * but not edited.
 *
 * @param props - `photos` are the User's Shared Photos, newest first, and
 *   `timeZone` is the User's time zone.
 * @returns The tab's content.
 */
export function SharedPhotosList({
  photos,
  timeZone,
}: {
  photos: SharedPhoto[];
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
    <div className="flex flex-col gap-6">
      <p className="m-0 text-caption text-ink-muted">
        Photos you sent that Zeph thought mattered to you, with a note on why.
        Zeph tries to leave out screenshots, receipts and memes. They stay until
        you delete them.
      </p>

      {deletePhoto.isError ? (
        <p role="alert" className="m-0 text-sm text-danger-deep">
          We couldn’t delete that. Please try again.
        </p>
      ) : null}

      {photos.length > 0 ? (
        <ol className="m-0 grid list-none grid-cols-1 gap-4 p-0 sm:grid-cols-2">
          {photos.map((photo) => {
            const day = formatWeekdayDay(photo.sent_at, timeZone);
            return (
              <li
                key={photo.id}
                aria-label={`Photo from ${day}`}
                className="flex flex-col gap-4 rounded-card border border-line bg-white p-4"
              >
                <SharedPhotoPicture photo={photo} />
                <div className="flex items-start gap-4">
                  <span className="flex min-w-0 flex-auto flex-col gap-2">
                    <span className="text-caption font-semibold text-ink-body">
                      {day}
                    </span>
                    <span className="text-[15px]">{photo.description}</span>
                    <span className="text-caption text-ink-soft">
                      {photo.note}
                    </span>
                  </span>
                  <button
                    type="button"
                    aria-label={`Delete photo from ${day}`}
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
        <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
          <span className="text-[22px] font-medium tracking-[-0.02em]">
            No photos kept yet
          </span>
          <p className="m-0 text-caption text-ink-muted">
            When you send Zeph a photo that matters to you, it may keep it here
            after the Conversation ends.
          </p>
        </div>
      )}
    </div>
  );
}
