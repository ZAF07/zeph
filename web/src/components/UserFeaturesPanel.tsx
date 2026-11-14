"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { compactSecondaryButton } from "@/components/button-styles";
import { LoadFailed } from "@/components/LoadFailed";
import type {
  AdminUser,
  UserFeatures,
  UserFeatureStatus,
  UserFeatureSwitch,
} from "@/lib/api-client";
import { lastChangeNote, reasonText } from "@/lib/features";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const switchOptions: { id: UserFeatureSwitch; label: string }[] = [
  { id: "default", label: "Default" },
  { id: "on", label: "On" },
  { id: "off", label: "Off" },
];

/**
 * The Features panel for one User: one row per Feature with its switch for
 * them (default, on or off), whether it works for them now and why, and the
 * last change, and how many Personal Stickers the User has (never which). A
 * switch saves as soon as it is picked. Escape closes the panel, unless a
 * change is being saved.
 *
 * @param props - `user` is the User whose Features are shown; `onClose`
 *   closes the panel.
 * @returns The panel as a dialog.
 */
export function UserFeaturesPanel({
  user,
  onClose,
}: {
  user: AdminUser;
  onClose: () => void;
}) {
  const apiClient = useApiClient();
  const closeRef = useRef<HTMLButtonElement>(null);
  const queryClient = useQueryClient();
  const displayName = user.name ?? user.email ?? "This User";
  const userFeaturesKey = queryKeys.userFeatures(user.id);

  const featuresQuery = useQuery({
    queryKey: userFeaturesKey,
    queryFn: () => apiClient.listUserFeatures(user.id),
  });
  const userFeatures = featuresQuery.data;

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
      void queryClient.invalidateQueries({ queryKey: queryKeys.me });
    },
  });
  const isSaving = setSwitch.isPending;
  const failedFeature = setSwitch.isError ? setSwitch.variables.feature : null;

  useEffect(() => {
    closeRef.current?.focus();
  }, []);

  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && !isSaving) {
        onClose();
      }
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => document.removeEventListener("keydown", closeOnEscape);
  }, [isSaving, onClose]);

  function changeSwitch(
    feature: UserFeatureStatus,
    featureSwitch: UserFeatureSwitch,
  ) {
    if (feature.switch !== featureSwitch) {
      setSwitch.mutate({ feature, featureSwitch });
    }
  }

  return (
    <div className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="user-features-heading"
        className="flex max-h-[min(90vh,720px)] w-full max-w-[640px] flex-col gap-4 overflow-y-auto rounded-panel bg-white p-6 shadow-xl"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 flex-col gap-1">
            <h2
              id="user-features-heading"
              className="m-0 text-h3 font-semibold"
            >
              Features for {displayName}
            </h2>
            {user.name && user.email ? (
              <p className="m-0 break-all text-caption text-ink-muted">
                {user.email}
              </p>
            ) : null}
          </div>
          <button
            ref={closeRef}
            type="button"
            className={compactSecondaryButton}
            disabled={isSaving}
            onClick={onClose}
          >
            Close
          </button>
        </div>
        <p className="m-0 text-caption text-ink-muted">
          Default follows the switch for everyone. On or Off applies to this
          User only.
        </p>

        {featuresQuery.isPending ? (
          <div
            aria-busy="true"
            aria-label="Loading Features"
            className="h-[96px] rounded-card border border-line bg-subtle"
          />
        ) : null}

        {!userFeatures && featuresQuery.isError ? (
          <LoadFailed
            title="Couldn’t load Features"
            body="This User’s switches are unchanged."
            onRetry={() => void featuresQuery.refetch()}
          />
        ) : null}

        {failedFeature ? (
          <p
            role="alert"
            className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
          >
            Couldn’t change {failedFeature.name} for {displayName}. It is still{" "}
            {failedFeature.switch}.
          </p>
        ) : null}

        {userFeatures ? (
          <ul className="m-0 flex list-none flex-col rounded-card border border-line p-0">
            {userFeatures.features.map((feature, index) => (
              <li
                key={feature.feature}
                className={`flex flex-wrap items-center justify-between gap-x-5 gap-y-3 px-5 py-4 ${
                  index > 0 ? "border-t border-line" : ""
                }`}
              >
                <span className="flex min-w-0 flex-[1_1_220px] flex-col gap-0.5">
                  <span className="font-semibold">{feature.name}</span>
                  <span
                    className={`text-caption ${
                      feature.works ? "text-blue-deep" : "text-ink-muted"
                    }`}
                  >
                    {reasonText(feature.reason)}
                  </span>
                  {feature.switch !== "default" ? (
                    <span className="text-caption text-ink-muted">
                      {lastChangeNote(feature)}
                    </span>
                  ) : null}
                </span>
                <span
                  role="group"
                  aria-label={`${feature.name} for ${displayName}`}
                  className="flex gap-1.5"
                >
                  {switchOptions.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      aria-pressed={feature.switch === option.id}
                      disabled={isSaving}
                      onClick={() => changeSwitch(feature, option.id)}
                      className={`min-h-10 cursor-pointer rounded-full border px-3.5 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60 ${
                        feature.switch === option.id
                          ? "border-ink bg-ink text-white"
                          : "border-line-strong bg-transparent text-ink-body"
                      }`}
                    >
                      {option.label}
                    </button>
                  ))}
                </span>
              </li>
            ))}
          </ul>
        ) : null}

        {userFeatures ? (
          <p className="m-0 text-caption text-ink-muted">
            Personal Stickers kept for {displayName}:{" "}
            {userFeatures.personal_sticker_count}
          </p>
        ) : null}
      </div>
    </div>
  );
}
