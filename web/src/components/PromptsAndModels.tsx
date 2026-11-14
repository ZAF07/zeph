"use client";

import { useQuery } from "@tanstack/react-query";

import { CoreServiceCard } from "@/components/CoreServiceCard";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import { queryKeys } from "@/lib/queries";
import { useAdminSettings } from "@/lib/use-admin-settings";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Prompts & models page: one card per core service, each with its
 * model and prompt.
 *
 * @returns The cards, or a loading, empty or error state.
 */
export function PromptsAndModels() {
  const apiClient = useApiClient();
  const settingsQuery = useAdminSettings();
  const servicesQuery = useQuery({
    queryKey: queryKeys.coreServices,
    queryFn: () => apiClient.getCoreServices(),
  });
  const settings = settingsQuery.data;
  const coreServices = servicesQuery.data;

  if (!settings || !coreServices) {
    if (settingsQuery.isError || servicesQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load prompts"
          body="Every service keeps running on its last saved prompt and model."
          onRetry={() => {
            void servicesQuery.refetch();
            void settingsQuery.refetch();
          }}
        />
      );
    }
    return (
      <div
        aria-busy="true"
        aria-label="Loading services"
        className="h-[360px] rounded-card border border-line bg-subtle"
      />
    );
  }

  const { services, model_choices: modelChoices } = coreServices;
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
            settings={settings}
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
