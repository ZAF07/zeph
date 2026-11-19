"use client";

import { useState } from "react";

import { ApiError } from "@/lib/api-client";

/** A card's save or remove under way, and why the last one failed. */
export type CardAction = {
  isBusy: boolean;
  failedMessage: string | null;
  run: (action: () => Promise<void>, failureText: string) => Promise<void>;
  clearFailure: () => void;
};

/**
 * Runs a card's save or remove, one at a time. When it fails, it keeps the
 * backend's reason for a refused change (a 422 or 409 with a detail), or
 * the given words.
 *
 * @returns Whether one is under way, why the last failed, and `run`.
 */
export function useCardAction(): CardAction {
  const [isBusy, setIsBusy] = useState(false);
  const [failedMessage, setFailedMessage] = useState<string | null>(null);

  async function run(action: () => Promise<void>, failureText: string) {
    setIsBusy(true);
    setFailedMessage(null);
    try {
      await action();
    } catch (failure) {
      const refusedReason =
        failure instanceof ApiError &&
        (failure.status === 422 || failure.status === 409)
          ? failure.detail
          : null;
      setFailedMessage(refusedReason || failureText);
    } finally {
      setIsBusy(false);
    }
  }

  return {
    isBusy,
    failedMessage,
    run,
    clearFailure: () => setFailedMessage(null),
  };
}
