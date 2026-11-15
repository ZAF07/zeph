"use client";

import { useMutation } from "@tanstack/react-query";
import Image from "next/image";

import { compactSecondaryButton } from "@/components/button-styles";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";
import { useImageUrl } from "@/lib/use-image-url";

/**
 * A photo case's image: a preview of the one chosen and a file picker that
 * uploads a new one. An upload is kept under a new name, so old runs keep
 * showing the image they used.
 *
 * @param props - `inputId` labels the file picker, `name` is the chosen
 *   image's name (null for none), `disabled` locks it and `onChange` gets
 *   the new image's name, or null when it is cleared.
 * @returns The field.
 */
export function EvalImageField({
  inputId,
  name,
  disabled,
  onChange,
}: {
  inputId: string;
  name: string | null;
  disabled: boolean;
  onChange: (name: string | null) => void;
}) {
  const apiClient = useApiClient();
  const image = useImageUrl(
    queryKeys.evalImage(name ?? ""),
    () => apiClient.getEvalImage(name ?? ""),
    name !== null,
  );
  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadEvalImage(file),
    onSuccess: (uploaded) => onChange(uploaded.name),
  });

  return (
    <div className="flex flex-col gap-2.5">
      {name ? (
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative size-24 overflow-hidden rounded-input border border-line bg-subtle">
            {image.url ? (
              <Image
                src={image.url}
                alt={`Test image ${name}`}
                fill
                sizes="96px"
                unoptimized
                className="object-cover"
              />
            ) : null}
          </div>
          <span className="font-mono text-caption text-ink-muted">{name}</span>
          <button
            type="button"
            className={compactSecondaryButton}
            disabled={disabled}
            onClick={() => onChange(null)}
          >
            Remove image
          </button>
        </div>
      ) : null}
      <input
        id={inputId}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        disabled={disabled || uploadMutation.isPending}
        className="text-caption"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) {
            uploadMutation.mutate(file);
          }
        }}
      />
      {uploadMutation.isPending ? (
        <p className="m-0 text-caption text-ink-muted">Uploading…</p>
      ) : null}
      {uploadMutation.isError ? (
        <p role="alert" className="m-0 text-caption text-danger">
          Couldn’t upload it. Use a PNG, JPEG or WebP image of at most 5 MB.
        </p>
      ) : null}
    </div>
  );
}
