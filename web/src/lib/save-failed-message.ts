import { ApiError } from "@/lib/api-client";

/** What the save bar says when a save fails for no reason the backend gave. */
export const SAVE_FAILED_MESSAGE = "Couldn’t save. Your text is still here.";

/**
 * Says why a save failed, for the save bar: the backend's reason when it
 * refused the values, otherwise the design's fixed words.
 *
 * @param error - The save's error, or null if it hasn't failed.
 * @returns The message, or null when the save hasn't failed.
 */
export function saveFailedMessage(error: Error | null): string | null {
  if (!error) {
    return null;
  }
  if (error instanceof ApiError && error.status === 422 && error.detail) {
    return error.detail;
  }
  return SAVE_FAILED_MESSAGE;
}
