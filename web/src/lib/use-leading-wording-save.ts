"use client";

import { useState } from "react";

import { leadingFlagsOf } from "@/lib/thought-experiment-draft";
import type { CardAction } from "@/lib/use-card-action";

/** A Thought Experiment save that may be refused for leading wording. */
export type LeadingWordingSave = {
  flags: string[] | null;
  save: (
    attempt: (saveAnyway: boolean) => Promise<void>,
    saveAnyway: boolean,
  ) => void;
  dismiss: () => void;
};

/**
 * Runs a Thought Experiment save through a card's action. When the backend
 * refuses it for leading wording, it keeps the leading phrases instead of
 * a failure, so the card can ask whether to save it anyway.
 *
 * @param action - The card's action, for busy and failure.
 * @param failureText - The words for any other failure.
 * @returns The leading phrases of the last refused save, if any; `save`,
 *   which runs one try, saving anyway or not; and `dismiss`.
 */
export function useLeadingWordingSave(
  action: CardAction,
  failureText: string,
): LeadingWordingSave {
  const [flags, setFlags] = useState<string[] | null>(null);

  function save(
    attempt: (saveAnyway: boolean) => Promise<void>,
    saveAnyway: boolean,
  ) {
    setFlags(null);
    void action.run(async () => {
      try {
        await attempt(saveAnyway);
      } catch (failure) {
        const leading = leadingFlagsOf(failure);
        if (!leading) {
          throw failure;
        }
        setFlags(leading);
      }
    }, failureText);
  }

  return { flags, save, dismiss: () => setFlags(null) };
}
