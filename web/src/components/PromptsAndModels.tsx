"use client";

import { useCallback, useEffect, useState } from "react";

import { CoreServiceCard } from "@/components/CoreServiceCard";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import type { CoreServices } from "@/lib/api-client";
import { useAdminSettings } from "@/lib/use-admin-settings";
import { useApiClient } from "@/lib/use-api-client";

type ServicesState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; coreServices: CoreServices };

/**
 * The admin Prompts & models page: one card per core service, each with its
 * model and prompt.
 *
 * @returns The cards, or a loading, empty or error state.
 */
export function PromptsAndModels() {
  const apiClient = useApiClient();
  const {
    state: settingsState,
    reload: reloadSettings,
    save,
  } = useAdminSettings();
  const [servicesState, setServicesState] = useState<ServicesState>({
    kind: "loading",
  });

  const loadServices = useCallback(async () => {
    setServicesState({ kind: "loading" });
    try {
      setServicesState({
        kind: "loaded",
        coreServices: await apiClient.getCoreServices(),
      });
    } catch {
      setServicesState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void loadServices();
  }, [loadServices]);

  if (servicesState.kind === "failed" || settingsState.kind === "failed") {
    return (
      <LoadFailed
        title="Couldn’t load prompts"
        body="Every service keeps running on its last saved prompt and model."
        onRetry={() => {
          void loadServices();
          reloadSettings();
        }}
      />
    );
  }

  if (servicesState.kind === "loading" || settingsState.kind === "loading") {
    return (
      <div
        aria-busy="true"
        aria-label="Loading services"
        className="h-[360px] rounded-card border border-line bg-subtle"
      />
    );
  }

  const { services, model_choices: modelChoices } = servicesState.coreServices;
  if (services.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-line-strong px-6 py-16 text-center">
        <span className="text-[22px] font-medium tracking-[-0.02em]">
          No services configured
        </span>
        <p className="m-0 text-caption text-ink-muted">
          Core services appear here once the backend registers them.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-[repeat(auto-fit,minmax(min(480px,100%),1fr))] gap-5">
        {services.map((service) => (
          <CoreServiceCard
            key={service.name}
            service={service}
            modelChoices={modelChoices}
            settings={settingsState.settings}
            onSave={save}
          />
        ))}
      </div>
      <p className="m-0 text-caption text-ink-muted">
        <span className="inline-flex items-center gap-1.5 text-xs font-medium">
          <LockIcon />
          No message content
        </span>{" "}
        — there’s no test console with real Conversations here by design.
      </p>
    </>
  );
}
