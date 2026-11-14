"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

/**
 * Loads an image through the API client and gives a URL an `<img>` can
 * show. The image is loaded once per key; the URL is freed when the
 * component goes.
 *
 * @param queryKey - The image's cache key, from `queryKeys`.
 * @param loadImage - Loads the image from the backend.
 * @param hasImage - False when there is no image to load.
 * @returns `url` once loaded, else null; `failed` when it couldn't load.
 */
export function useImageUrl(
  queryKey: readonly unknown[],
  loadImage: () => Promise<Blob>,
  hasImage = true,
): { url: string | null; failed: boolean } {
  const image = useQuery({
    queryKey,
    queryFn: loadImage,
    enabled: hasImage,
    staleTime: Infinity,
  });
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    if (!image.data) {
      return;
    }
    const objectUrl = URL.createObjectURL(image.data);
    setUrl(objectUrl);
    return () => {
      URL.revokeObjectURL(objectUrl);
      setUrl(null);
    };
  }, [image.data]);

  return { url, failed: image.isError };
}
