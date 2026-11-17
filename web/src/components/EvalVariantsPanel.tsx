"use client";

import { useQuery } from "@tanstack/react-query";

import { EvalVariantCard } from "@/components/EvalVariantCard";
import type { EvalRunDetails } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import {
  moveOverridePrefix,
  needOverridePrefix,
  overrideLabel,
} from "@/lib/setting-overrides";
import { useApiClient } from "@/lib/use-api-client";

/**
 * A run's Variants, each with its Setting Overrides shown as a difference
 * from the live settings when the run started, and Make Live once the run
 * has finished. A run of the live settings alone shows nothing here.
 *
 * @param props - `run` is the run.
 * @returns The Variants, or nothing for a plain run.
 */
export function EvalVariantsPanel({ run }: { run: EvalRunDetails }) {
  const apiClient = useApiClient();
  const isPlain =
    run.variants.length === 1 &&
    Object.keys(run.variants[0]?.setting_overrides ?? {}).length === 0;
  const choicesQuery = useQuery({
    queryKey: queryKeys.settingOverrideChoices,
    queryFn: () => apiClient.listSettingOverrideChoices(),
    enabled: !isPlain,
  });
  const snapshotQuery = useQuery({
    queryKey: queryKeys.evalRunSnapshot(run.id),
    queryFn: () => apiClient.getEvalRunSnapshot(run.id),
    enabled: !isPlain && run.state !== "queued",
  });

  if (isPlain) {
    return null;
  }
  const snapshot = snapshotQuery.data;

  function labelOf(key: string): string {
    return overrideLabel(key, choicesQuery.data, {
      needs: snapshot?.needs ?? [],
      moves: snapshot?.moves ?? [],
    });
  }

  function thenValueOf(key: string): unknown {
    if (!snapshot?.settings) {
      return undefined;
    }
    if (key.startsWith(needOverridePrefix)) {
      return snapshot.needs?.find((need) => need.key === key)?.value ?? null;
    }
    if (key.startsWith(moveOverridePrefix)) {
      return snapshot.moves?.find((move) => move.key === key)?.value ?? null;
    }
    return snapshot.settings[key] ?? null;
  }

  return (
    <div className="flex flex-col gap-2.5">
      {run.variants.map((variant) => (
        <EvalVariantCard
          key={variant.letter}
          runId={run.id}
          runState={run.state}
          variant={variant}
          labelOf={labelOf}
          thenValueOf={thenValueOf}
        />
      ))}
    </div>
  );
}
