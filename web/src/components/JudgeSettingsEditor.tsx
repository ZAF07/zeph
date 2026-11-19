"use client";

import { useQuery } from "@tanstack/react-query";

import { JudgeSettingsForm } from "@/components/JudgeSettingsForm";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
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
      <LoadingPanel shape="card" label="Loading the Judge’s settings" />
    );
  }
  return <JudgeSettingsForm settings={settings} />;
}
