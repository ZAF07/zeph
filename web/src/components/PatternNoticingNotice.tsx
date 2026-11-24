"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { secondaryButton } from "@/components/button-styles";
import { PausedNotice } from "@/components/PausedNotice";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { Me } from "@/lib/api-client";
import { type Copy, readCopy } from "@/lib/copy";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The notice telling a User that Zeph now keeps some of their words as
 * evidence, drawn as the design's notice row with a "Got it" button. Zeph
 * keeps no quote for them until they press it; then the notice goes.
 *
 * @param props - `me` is the signed-in User, whose `pattern_noticing_notice`
 *   says whether to show it, and `copy` holds the Shared
 *   `shared.pattern_noticing.` slots.
 * @returns The notice, or nothing once they have been told.
 */
export function PatternNoticingNotice({ me, copy }: { me: Me; copy: Copy }) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const markTold = useMutation({
    mutationFn: () => apiClient.markPatternNoticingTold(),
    onSuccess: (told) => queryClient.setQueryData(queryKeys.me, told),
  });

  if (!me.pattern_noticing_notice) {
    return null;
  }
  return (
    <div role="status" className="flex flex-col gap-2.5">
      <PausedNotice
        title={readCopy(copy, "shared.pattern_noticing.title")}
        body={readCopy(copy, "shared.pattern_noticing.body")}
        action={
          <button
            type="button"
            className={secondaryButton}
            disabled={markTold.isPending}
            onClick={() => markTold.mutate()}
          >
            {readCopy(copy, "shared.pattern_noticing.got_it")}
          </button>
        }
      />
      {markTold.isError ? (
        <SaveFailedNote>
          {readCopy(copy, "shared.pattern_noticing.save_failed")}
        </SaveFailedNote>
      ) : null}
    </div>
  );
}
