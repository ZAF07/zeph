"use client";

import { useCallback, useEffect, useState } from "react";

import { LoadFailed } from "@/components/LoadFailed";
import { Switch } from "@/components/Switch";
import type { Feature, FeatureSwitch } from "@/lib/api-client";
import { formatSavedAt } from "@/lib/dates";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; features: FeatureSwitch[] };

/**
 * Says who last changed a Feature's switch for everyone, and when.
 *
 * @param feature - The Feature's switch.
 * @returns A note like "Changed 13 Nov, 14:20 by maya@example.com", or
 *   "Never changed".
 */
function lastChangeNote(feature: FeatureSwitch): string {
  if (!feature.changed_at) {
    return "Never changed";
  }
  const changedBy = feature.changed_by ? ` by ${feature.changed_by}` : "";
  return `Changed ${formatSavedAt(feature.changed_at)}${changedBy}`;
}

/**
 * The admin Features page's body: one row per Feature with what it does, its
 * switch for everyone and its last change. A switch saves as soon as it is
 * flipped.
 *
 * @returns The list, or a loading block or error with Try again.
 */
export function AdminFeatures() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [saving, setSaving] = useState<Feature | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      setState({ kind: "loaded", features: await apiClient.listFeatures() });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  if (state.kind === "loading") {
    return (
      <div
        aria-busy="true"
        aria-label="Loading Features"
        className="h-[120px] rounded-card border border-line bg-subtle"
      />
    );
  }

  if (state.kind === "failed") {
    return (
      <LoadFailed
        title="Couldn’t load Features"
        body="Every Feature keeps its last saved switch."
        onRetry={() => void load()}
      />
    );
  }

  const features = state.features;

  async function switchForEveryone(feature: FeatureSwitch, on: boolean) {
    setSaving(feature.feature);
    setFailure(null);
    try {
      const changed = await apiClient.setFeatureForEveryone(
        feature.feature,
        on,
      );
      setState({
        kind: "loaded",
        features: features.map((current) =>
          current.feature === changed.feature ? changed : current,
        ),
      });
    } catch {
      setFailure(
        `Couldn’t change ${feature.name}. It is still ${feature.on ? "on" : "off"}.`,
      );
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {failure ? (
        <p
          role="alert"
          className="m-0 rounded-xl border border-danger-line bg-danger-tint px-4 py-3.5 text-sm text-danger-deep"
        >
          {failure}
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
                disabled={saving !== null}
                onChange={(on) => void switchForEveryone(feature, on)}
              />
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
