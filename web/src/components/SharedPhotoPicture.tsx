"use client";

import Image from "next/image";
import { useEffect, useState } from "react";

import type { SharedPhoto } from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

type ImageState =
  { kind: "loading" } | { kind: "failed" } | { kind: "loaded"; url: string };

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
  const [state, setState] = useState<ImageState>({ kind: "loading" });

  useEffect(() => {
    let objectUrl: string | null = null;
    let cancelled = false;
    apiClient
      .getSharedPhotoImage(photo.id)
      .then((image) => {
        if (!cancelled) {
          objectUrl = URL.createObjectURL(image);
          setState({ kind: "loaded", url: objectUrl });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState({ kind: "failed" });
        }
      });
    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [apiClient, photo.id]);

  if (state.kind === "loaded") {
    return (
      <div className="relative aspect-[4/3] overflow-hidden rounded-xl bg-subtle">
        <Image
          src={state.url}
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
      aria-busy={state.kind === "loading"}
      className="flex aspect-[4/3] items-center justify-center rounded-xl border border-dashed border-line-strong bg-subtle px-4 text-center text-caption text-ink-muted"
    >
      {state.kind === "failed" ? "This photo can’t be shown right now" : null}
    </div>
  );
}
