"use client";

import { useQuery } from "@tanstack/react-query";

import { CardCount } from "@/components/CardCount";
import { CardList } from "@/components/CardList";
import { CardListLoading } from "@/components/CardListLoading";
import { CoreServiceCard } from "@/components/CoreServiceCard";
import { EmptyState } from "@/components/EmptyState";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import { queryKeys } from "@/lib/queries";
import { useAdminSettings } from "@/lib/use-admin-settings";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Prompts & models page, from the card-list template: a folding
 * card per core service, each with its model and prompts. The first card
 * starts open.
 *
 * @returns The services, or a loading, empty or error state.
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
          body="Every service keeps running on its last saved prompt, model and thinking."
          onRetry={() => {
            void servicesQuery.refetch();
            void settingsQuery.refetch();
          }}
        />
      );
    }
    return <CardListLoading label="Loading services" />;
  }

  const { services, model_choices: modelChoices } = coreServices;
  if (services.length === 0) {
    return (
      <EmptyState
        title="No services configured"
        body="Core services appear here once the backend registers them."
      />
    );
  }

  return (
    <>
      <CardList
        items={services.map((service) => ({ id: service.prompt_key, service }))}
        count={
          <CardCount
            count={services.length}
            words={services.length === 1 ? "service" : "services"}
          />
        }
        renderCard={({ id, service }, _index, folding) => (
          <CoreServiceCard
            key={id}
            service={service}
            modelChoices={modelChoices}
            settings={settings}
            isOpen={folding.isOpen}
            onToggle={folding.onToggle}
          />
        )}
      />
      <p className="m-0 text-[13px] text-soft">
        <span className="inline-flex items-center gap-1.5 text-[12px] text-text">
          <LockIcon />
          No message content
        </span>{" "}
        — there’s no test console with real Conversations here by design.
      </p>
    </>
  );
}
