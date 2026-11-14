"use client";

import Image from "next/image";

import type { PersonalSticker } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";
import { useImageUrl } from "@/lib/use-image-url";

/**
 * A Personal Sticker's image, loaded through the API client. Shows the
 * sticker's emoji instead while it loads, or when it has no image or it
 * can't load.
 *
 * @param props - `sticker` is the User's Personal Sticker to show.
 * @returns The image, or its emoji in the same square.
 */
export function PersonalStickerPicture({
  sticker,
}: {
  sticker: PersonalSticker;
}) {
  const apiClient = useApiClient();
  const imageUrl = useImageUrl(
    queryKeys.personalStickerImage(sticker.id),
    () => apiClient.getPersonalStickerImage(sticker.id),
    sticker.has_image,
  ).url;
  const label = `Sticker: ${sticker.emoji ?? "no emoji"}`;

  if (imageUrl) {
    return (
      <div className="relative aspect-square w-20 flex-none overflow-hidden rounded-xl bg-subtle">
        <Image
          src={imageUrl}
          alt={label}
          fill
          sizes="80px"
          unoptimized
          className="object-contain p-1.5"
        />
      </div>
    );
  }
  return (
    <div
      role="img"
      aria-label={label}
      className="flex aspect-square w-20 flex-none items-center justify-center rounded-xl border border-dashed border-line-strong bg-subtle text-[36px]"
    >
      {sticker.emoji}
    </div>
  );
}
