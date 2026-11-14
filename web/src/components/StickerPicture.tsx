"use client";

import Image from "next/image";

import type { Sticker } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";
import { useImageUrl } from "@/lib/use-image-url";

/**
 * A sticker's image, loaded through the API client. Shows the sticker's
 * emoji instead while it loads, or when it has no image or it can't load.
 *
 * @param props - `sticker` is the Sticker Library sticker to show.
 * @returns The image, or its emoji in the same square.
 */
export function StickerPicture({ sticker }: { sticker: Sticker }) {
  const apiClient = useApiClient();
  const imageUrl = useImageUrl(
    queryKeys.stickerImage(sticker.id),
    () => apiClient.getStickerImage(sticker.id),
    sticker.has_image,
  ).url;
  const label = `Sticker: ${sticker.emoji ?? "no emoji"}`;

  if (imageUrl) {
    return (
      <div className="relative aspect-square overflow-hidden rounded-xl bg-subtle">
        <Image
          src={imageUrl}
          alt={label}
          fill
          sizes="200px"
          unoptimized
          className="object-contain p-2"
        />
      </div>
    );
  }
  return (
    <div
      role="img"
      aria-label={label}
      className="flex aspect-square items-center justify-center rounded-xl border border-dashed border-line-strong bg-subtle text-[56px]"
    >
      {sticker.emoji}
    </div>
  );
}
