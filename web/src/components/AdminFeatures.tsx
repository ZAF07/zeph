"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { FieldRow } from "@/components/FieldRow";
import { FieldRows } from "@/components/FieldRows";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { Switch } from "@/components/Switch";
import type { FeatureSwitch } from "@/lib/api-client";
import { lastChangeNote } from "@/lib/features";
import { queryKeys, reloadUserPages } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Features page's body: one field row per Feature with what it
 * does, its last change and its switch for everyone. A switch saves as soon as it is
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
      reloadUserPages(queryClient);
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
    return <LoadingPanel shape="card" label="Loading Features" />;
  }

  const failedFeature = switchForEveryone.isError
    ? switchForEveryone.variables.feature
    : null;

  return (
    <>
      {failedFeature ? (
        <SaveFailedNote>
          Couldn’t change {failedFeature.name}. It is still{" "}
          {failedFeature.on ? "on" : "off"}.
        </SaveFailedNote>
      ) : null}
      <FieldRows>
        {features.map((feature) => (
          <FieldRow
            key={feature.feature}
            title={feature.name}
            caption={feature.description}
            note={
              <div className="text-[12px] text-soft">
                {lastChangeNote(feature)}
              </div>
            }
          >
            <Switch
              label={`${feature.name} for everyone`}
              checked={feature.on}
              disabled={switchForEveryone.isPending}
              onChange={(on) => switchForEveryone.mutate({ feature, on })}
            />
          </FieldRow>
        ))}
      </FieldRows>
    </>
  );
}
