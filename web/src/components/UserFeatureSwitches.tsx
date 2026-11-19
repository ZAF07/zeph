"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { Switch } from "@/components/Switch";
import type {
  AdminUser,
  UserFeatures,
  UserFeatureStatus,
  UserFeatureSwitch,
} from "@/lib/api-client";
import {
  isOnForUser,
  lastChangeNote,
  switchForUser,
  userFeatureLine,
} from "@/lib/features";
import { queryKeys, reloadUserPages } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";
import { displayNameOf } from "@/lib/users";

/**
 * One User's Feature switches in the Users side panel: one row per Feature
 * with whether it works for them and why, and a switch. The switch is on
 * when the Admin's switches let the Feature work for the User. Turning it
 * to match everyone's switch saves Default; otherwise it saves On or Off for
 * this User. A switch saves as soon as it is flipped.
 *
 * @param props - `user` is the User whose Features are shown.
 * @returns The switch rows, or a loading or error state.
 */
export function UserFeatureSwitches({ user }: { user: AdminUser }) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const displayName = displayNameOf(user);
  const userFeaturesKey = queryKeys.userFeatures(user.id);

  const userFeaturesQuery = useQuery({
    queryKey: userFeaturesKey,
    queryFn: () => apiClient.listUserFeatures(user.id),
  });
  const everyoneQuery = useQuery({
    queryKey: queryKeys.features,
    queryFn: () => apiClient.listFeatures(),
  });
  const userFeatures = userFeaturesQuery.data;
  const everyone = everyoneQuery.data;

  const setSwitch = useMutation({
    mutationFn: ({
      feature,
      featureSwitch,
    }: {
      feature: UserFeatureStatus;
      featureSwitch: UserFeatureSwitch;
    }) => apiClient.setFeatureForUser(user.id, feature.feature, featureSwitch),
    onSuccess: (changed) => {
      queryClient.setQueryData<UserFeatures>(userFeaturesKey, (current) =>
        current
          ? {
              ...current,
              features: current.features.map((status) =>
                status.feature === changed.feature ? changed : status,
              ),
            }
          : current,
      );
      reloadUserPages(queryClient);
    },
  });
  const failedFeature = setSwitch.isError ? setSwitch.variables.feature : null;

  /**
   * Tells whether a Feature is on for everyone.
   *
   * @param feature - The Feature's status for the User.
   * @returns True when everyone's switch is on.
   */
  function isOnForEveryone(feature: UserFeatureStatus): boolean {
    return (
      everyone?.find((each) => each.feature === feature.feature)?.on ?? false
    );
  }

  if (userFeaturesQuery.isPending || everyoneQuery.isPending) {
    return <LoadingPanel shape="card" label="Loading Features" />;
  }

  if (!userFeatures || !everyone) {
    return (
      <LoadFailed
        title="Couldn’t load Features"
        body="This User’s switches are unchanged."
        onRetry={() => {
          void userFeaturesQuery.refetch();
          void everyoneQuery.refetch();
        }}
      />
    );
  }

  return (
    <>
      {failedFeature ? (
        <SaveFailedNote>
          Couldn’t change {failedFeature.name} for {displayName}. It is still{" "}
          {isOnForUser(failedFeature.switch, isOnForEveryone(failedFeature))
            ? "on"
            : "off"}
          .
        </SaveFailedNote>
      ) : null}
      {userFeatures.features.map((feature, index) => {
        const isOn = isOnForUser(feature.switch, isOnForEveryone(feature));
        return (
          <div
            key={feature.feature}
            className={`flex items-center justify-between gap-3 ${
              index > 0 ? "border-t border-line" : ""
            }`}
          >
            <div>
              <div className="text-[14px] text-text">{feature.name}</div>
              <div className="text-[12px] text-soft">
                {userFeatureLine(feature, userFeatures.personal_sticker_count)}
              </div>
              {feature.switch !== "default" ? (
                <div className="text-[12px] text-soft">
                  {lastChangeNote(feature)}
                </div>
              ) : null}
            </div>
            <Switch
              label={`${feature.name} for this user`}
              checked={isOn}
              disabled={setSwitch.isPending}
              onChange={(turnOn) =>
                setSwitch.mutate({
                  feature,
                  featureSwitch: switchForUser(
                    turnOn,
                    isOnForEveryone(feature),
                  ),
                })
              }
            />
          </div>
        );
      })}
    </>
  );
}
