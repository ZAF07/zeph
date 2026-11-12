"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

import type { Sticker } from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

/**
 * A sticker's image, loaded through the API client. Shows the sticker's
 * emoji instead while it loads, or when it has no image or it can't load.
 *
 * @param props - `sticker` is the Sticker Library sticker to show.
 * @returns The image, or its emoji in the same square.
 */
export function StickerPicture({ sticker }: { sticker: Sticker }) {
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
      .getStickerImage(sticker.id)
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
      <div className="flex aspect-square items-center justify-center rounded-xl bg-subtle p-2">
        <Image
          src={imageUrl}
          alt={label}
          width={200}
          height={200}
          unoptimized
          className="size-full object-contain"
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
