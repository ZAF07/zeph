"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { compactSecondaryButton } from "@/components/button-styles";
import { LoadFailed } from "@/components/LoadFailed";
import type {
  AdminUser,
  UserFeatureStatus,
  UserFeatureSwitch,
} from "@/lib/api-client";
import { lastChangeNote, reasonText } from "@/lib/features";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; features: UserFeatureStatus[] };

const switchOptions: { id: UserFeatureSwitch; label: string }[] = [
  { id: "default", label: "Default" },
  { id: "on", label: "On" },
  { id: "off", label: "Off" },
];

/**
 * The Features panel for one User: one row per Feature with its switch for
 * them (default, on or off), whether it works for them now and why, and the
 * last change. A switch saves as soon as it is picked. Escape closes the
 * panel, unless a change is being saved.
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
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [isSaving, setIsSaving] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const displayName = user.name ?? user.email ?? "This User";

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      setState({
        kind: "loaded",
        features: await apiClient.listUserFeatures(user.id),
      });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient, user.id]);

  useEffect(() => {
    void load();
  }, [load]);

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

  async function setSwitch(
    feature: UserFeatureStatus,
    featureSwitch: UserFeatureSwitch,
  ) {
    if (feature.switch === featureSwitch) {
      return;
    }
    setIsSaving(true);
    setFailure(null);
    try {
      const changed = await apiClient.setFeatureForUser(
        user.id,
        feature.feature,
        featureSwitch,
      );
      setState((current) =>
        current.kind === "loaded"
          ? {
              kind: "loaded",
              features: current.features.map((status) =>
                status.feature === changed.feature ? changed : status,
              ),
            }
          : current,
      );
    } catch {
      setFailure(
        `Couldn’t change ${feature.name} for ${displayName}. It is still ${feature.switch}.`,
      );
    } finally {
      setIsSaving(false);
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

        {state.kind === "loading" ? (
          <div
            aria-busy="true"
            aria-label="Loading Features"
            className="h-[96px] rounded-card border border-line bg-subtle"
          />
        ) : null}

        {state.kind === "failed" ? (
          <LoadFailed
            title="Couldn’t load Features"
            body="This User’s switches are unchanged."
            onRetry={() => void load()}
          />
        ) : null}

        {failure ? (
          <p
            role="alert"
            className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
          >
            {failure}
          </p>
        ) : null}

        {state.kind === "loaded" ? (
          <ul className="m-0 flex list-none flex-col rounded-card border border-line p-0">
            {state.features.map((feature, index) => (
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
                      onClick={() => void setSwitch(feature, option.id)}
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
      </div>
    </div>
  );
}
