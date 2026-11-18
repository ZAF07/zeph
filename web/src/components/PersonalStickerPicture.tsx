"use client";

import Image from "next/image";

import type { PersonalSticker } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";
import { useImageUrl } from "@/lib/use-image-url";

/**
 * A Personal Sticker's image, loaded through the API client. Shows the
 * drawn dashed box instead while it loads, or when it has no image or it
 * can't load, with the sticker's emoji or the word "Sticker".
 *
 * @param props - `sticker` is the User's Personal Sticker to show.
 * @returns The image, or the dashed box in the same square.
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
  const label = sticker.emoji ? `Sticker: ${sticker.emoji}` : "Sticker";

  if (imageUrl) {
    return (
      <div className="relative box-content size-14 flex-none overflow-hidden rounded-input border border-transparent">
        <Image
          src={imageUrl}
          alt={label}
          fill
          sizes="56px"
          unoptimized
          className="object-contain"
        />
      </div>
    );
  }
  return (
    <div
      role="img"
      aria-label={label}
      className="box-content flex size-14 flex-none items-center justify-center rounded-input border border-dashed border-line-strong text-[11px] text-soft"
    >
      {sticker.emoji ?? "Sticker"}
    </div>
  );
}
