"use client";

import { useQuery } from "@tanstack/react-query";

import { JudgeSettingsForm } from "@/components/JudgeSettingsForm";
import { LoadFailed } from "@/components/LoadFailed";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * Loads the Judge's settings and their form, then shows the form.
 *
 * @returns The form, or a loading or error state.
 */
export function JudgeSettingsEditor() {
  const apiClient = useApiClient();
  const judgeQuery = useQuery({
    queryKey: queryKeys.judgeSettings,
    queryFn: () => apiClient.getJudgeSettings(),
  });
  const settings = judgeQuery.data;

  if (settings === undefined) {
    return judgeQuery.isError ? (
      <LoadFailed
        title="Couldn’t load the Judge’s settings"
        body="Nothing was changed."
        onRetry={() => void judgeQuery.refetch()}
      />
    ) : (
      <div
        aria-busy="true"
        aria-label="Loading the Judge’s settings"
        className="h-[420px] rounded-xl border border-line bg-subtle"
      />
    );
  }
  return <JudgeSettingsForm settings={settings} />;
}
