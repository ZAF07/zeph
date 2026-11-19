"use client";

import Image from "next/image";

import type { SharedPhoto } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";
import { useImageUrl } from "@/lib/use-image-url";

/**
 * A Shared Photo's image in a 120px square, loaded through the API client.
 * While it loads the square is the drawn dashed "Photo" box; when it can't
 * load, the box says so.
 *
 * @param props - `photo` is the Shared Photo to show, its description being
 *   the image's alt text; `label` names the placeholder box for screen
 *   readers, such as "Photo from 9 Nov"; `loadingText` is the box's words
 *   while it loads and `failedText` when it can't load.
 * @returns The image, or a placeholder in the same square.
 */
export function SharedPhotoPicture({
  photo,
  label,
  loadingText,
  failedText,
}: {
  photo: SharedPhoto;
  label: string;
  loadingText: string;
  failedText: string;
}) {
  const apiClient = useApiClient();
  const image = useImageUrl(queryKeys.sharedPhotoImage(photo.id), () =>
    apiClient.getSharedPhotoImage(photo.id),
  );

  if (image.url) {
    return (
      <div className="relative box-content size-[120px] flex-none overflow-hidden rounded-note border border-transparent">
        <Image
          src={image.url}
          alt={photo.description}
          fill
          sizes="120px"
          unoptimized
          className="object-cover"
        />
      </div>
    );
  }
  return (
    <div
      role="img"
      aria-label={label}
      aria-busy={!image.failed}
      className="box-content flex size-[120px] flex-none items-center justify-center rounded-note border border-dashed border-line-strong text-center text-[12px] text-soft"
    >
      {image.failed ? failedText : loadingText}
    </div>
  );
}
