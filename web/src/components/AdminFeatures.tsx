"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { LoadFailed } from "@/components/LoadFailed";
import { Switch } from "@/components/Switch";
import type { FeatureSwitch } from "@/lib/api-client";
import { lastChangeNote } from "@/lib/features";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Features page's body: one row per Feature with what it does, its
 * switch for everyone and its last change. A switch saves as soon as it is
 * flipped, and the signed-in Admin's own pages load again, since the
 * Feature may have changed for them too.
 *
 * @returns The list, or a loading block or error with Try again.
 */
export function AdminFeatures() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const featuresQuery = useQuery({
    queryKey: queryKeys.features,
    queryFn: () => apiClient.listFeatures(),
  });
  const switchForEveryone = useMutation({
    mutationFn: ({ feature, on }: { feature: FeatureSwitch; on: boolean }) =>
      apiClient.setFeatureForEveryone(feature.feature, on),
    onSuccess: (changed) => {
      queryClient.setQueryData<FeatureSwitch[]>(queryKeys.features, (current) =>
        current?.map((feature) =>
          feature.feature === changed.feature ? changed : feature,
        ),
      );
      void queryClient.invalidateQueries({ queryKey: queryKeys.me });
      void queryClient.invalidateQueries({ queryKey: queryKeys.home });
    },
  });
  const features = featuresQuery.data;

  if (!features) {
    if (featuresQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Features"
          body="Every Feature keeps its last saved switch."
          onRetry={() => void featuresQuery.refetch()}
        />
      );
    }
    return (
      <div
        aria-busy="true"
        aria-label="Loading Features"
        className="h-[120px] rounded-card border border-line bg-subtle"
      />
    );
  }

  const failedFeature = switchForEveryone.isError
    ? switchForEveryone.variables.feature
    : null;

  return (
    <div className="flex flex-col gap-4">
      {failedFeature ? (
        <p
          role="alert"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          Couldn’t change {failedFeature.name}. It is still{" "}
          {failedFeature.on ? "on" : "off"}.
        </p>
      ) : null}
      <ul className="m-0 flex list-none flex-col rounded-card border border-line bg-white p-0">
        {features.map((feature, index) => (
          <li
            key={feature.feature}
            className={`flex flex-wrap items-center justify-between gap-x-5 gap-y-3 px-5 py-4 ${
              index > 0 ? "border-t border-line" : ""
            }`}
          >
            <span className="flex min-w-0 flex-[1_1_260px] flex-col gap-0.5">
              <span className="font-semibold">{feature.name}</span>
              <span className="text-caption text-ink-muted">
                {feature.description}
              </span>
              <span className="text-caption text-ink-muted">
                {lastChangeNote(feature)}
              </span>
            </span>
            <span className="flex items-center gap-3">
              <span className="text-caption text-ink-muted" aria-hidden="true">
                {feature.on ? "On" : "Off"} for everyone
              </span>
              <Switch
                label={`${feature.name} for everyone`}
                checked={feature.on}
                disabled={switchForEveryone.isPending}
                onChange={(on) => switchForEveryone.mutate({ feature, on })}
              />
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
