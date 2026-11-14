"use client";

import Image from "next/image";

import type { SharedPhoto } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";
import { useImageUrl } from "@/lib/use-image-url";

/**
 * A Shared Photo's image, loaded through the API client. Shows a grey
 * square while it loads and a short note when it can't load.
 *
 * @param props - `photo` is the Shared Photo to show; its description is the
 *   image's alt text.
 * @returns The image, or a placeholder in the same square.
 */
export function SharedPhotoPicture({ photo }: { photo: SharedPhoto }) {
  const apiClient = useApiClient();
  const image = useImageUrl(queryKeys.sharedPhotoImage(photo.id), () =>
    apiClient.getSharedPhotoImage(photo.id),
  );

  if (image.url) {
    return (
      <div className="relative aspect-[4/3] overflow-hidden rounded-xl bg-subtle">
        <Image
          src={image.url}
          alt={photo.description}
          fill
          sizes="(max-width: 640px) 100vw, 320px"
          unoptimized
          className="object-cover"
        />
      </div>
    );
  }
  return (
    <div
      aria-busy={!image.failed}
      className="flex aspect-[4/3] items-center justify-center rounded-xl border border-dashed border-line-strong bg-subtle px-4 text-center text-caption text-ink-muted"
    >
      {image.failed ? "This photo can’t be shown right now" : null}
    </div>
  );
}
