"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

import type { PersonalSticker } from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

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
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const label = `Sticker: ${sticker.emoji ?? "no emoji"}`;

  useEffect(() => {
    if (!sticker.has_image) {
      return;
    }
    let objectUrl: string | null = null;
    let cancelled = false;
    apiClient
      .getPersonalStickerImage(sticker.id)
      .then((image) => {
        if (!cancelled) {
          objectUrl = URL.createObjectURL(image);
          setImageUrl(objectUrl);
        }
      })
      .catch(() => setImageUrl(null));
    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [apiClient, sticker.id, sticker.has_image]);

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
