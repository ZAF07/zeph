"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { SettingValueLine } from "@/components/SettingValueLine";
import { ApiError, type LiveChange } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The Make Live button of a Variant of a Finished run. Its Setting Overrides
 * are applied to the live settings through the normal settings save. When
 * no overridden setting changed live since the run started, one click
 * applies them all; otherwise the Admin sees each changed one's value then,
 * now and the override, and ticks the ones to apply anyway. The rest apply
 * straight away.
 *
 * @param props - `runId` is the run; `letter` the Variant's letter;
 *   `labelOf` names an overridden setting by its key.
 * @returns The button, or the confirm step.
 */
export function MakeLiveControl({
  runId,
  letter,
  labelOf,
}: {
  runId: string;
  letter: string;
  labelOf: (key: string) => string;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [changes, setChanges] = useState<LiveChange[] | null>(null);
  const [confirmed, setConfirmed] = useState<string[]>([]);
  const applyMutation = useMutation({
    mutationFn: (confirmedKeys: string[]) =>
      apiClient.makeVariantLive(runId, letter, confirmedKeys),
    onSuccess: () => {
      setChanges(null);
      void queryClient.invalidateQueries({
        queryKey: queryKeys.evalRun(runId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.settingOverrideChoices,
      });
    },
  });
  const checkMutation = useMutation({
    mutationFn: () => apiClient.listLiveChanges(runId, letter),
    onSuccess: (found) => {
      if (found.length === 0) {
        applyMutation.mutate([]);
      } else {
        setConfirmed([]);
        setChanges(found);
      }
    },
  });
  const error = checkMutation.error ?? applyMutation.error;
  const busy = checkMutation.isPending || applyMutation.isPending;

  function toggle(key: string) {
    setConfirmed(
      confirmed.includes(key)
        ? confirmed.filter((other) => other !== key)
        : [...confirmed, key],
    );
  }

  return (
    <div className="flex flex-col gap-2.5">
      {changes === null ? (
        <div>
          <button
            type="button"
            className={secondaryButton}
            disabled={busy}
            onClick={() => checkMutation.mutate()}
          >
            {busy ? "Making live…" : `Make Variant ${letter} live`}
          </button>
        </div>
      ) : (
        <section
          aria-label={`Confirm making Variant ${letter} live`}
          className="flex flex-col gap-3 rounded-tile border border-orange px-5 py-4"
        >
          <p className="m-0 text-[13px] text-orange">
            {changes.length === 1
              ? "This setting was changed live since the run started."
              : "These settings were changed live since the run started."}{" "}
            Tick the ones to replace anyway; the rest of Variant {letter}’s
            changes go live as they are.
          </p>
          {changes.map((change) => (
            <label
              key={change.key}
              className="flex cursor-pointer items-start gap-3 rounded-input border border-line bg-bg-deep px-3.5 py-2.5"
            >
              <input
                type="checkbox"
                className="mt-1 size-4 accent-cream"
                checked={confirmed.includes(change.key)}
                onChange={() => toggle(change.key)}
              />
              <span className="flex min-w-0 flex-col gap-1 text-[13px]">
                <span className="text-cream">
                  Replace {labelOf(change.key)}
                </span>
                <SettingValueLine
                  name="When the run started"
                  value={change.then}
                />
                <SettingValueLine name="Live now" value={change.now} />
                <SettingValueLine
                  name={`Variant ${letter}`}
                  value={change.override}
                />
              </span>
            </label>
          ))}
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className={primaryButton}
              disabled={busy}
              onClick={() => applyMutation.mutate(confirmed)}
            >
              {busy ? "Making live…" : "Make live"}
            </button>
            <button
              type="button"
              className={secondaryButton}
              disabled={busy}
              onClick={() => setChanges(null)}
            >
              Back
            </button>
          </div>
        </section>
      )}
      {error ? (
        <p role="alert" className="m-0 text-[13px] text-danger">
          {error instanceof ApiError && error.detail
            ? `Couldn’t make it live: ${error.detail}`
            : "Couldn’t make it live. Nothing was changed. Try again."}
        </p>
      ) : null}
    </div>
  );
}
