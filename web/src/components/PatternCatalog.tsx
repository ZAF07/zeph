"use client";

import { useQuery } from "@tanstack/react-query";

import { CardCount } from "@/components/CardCount";
import { CardList } from "@/components/CardList";
import { CardListLoading } from "@/components/CardListLoading";
import { EmptyState } from "@/components/EmptyState";
import { LoadFailed } from "@/components/LoadFailed";
import { LockIcon } from "@/components/LockIcon";
import { PatternTypeCard } from "@/components/PatternTypeCard";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Pattern Catalog page, from the card-list template: a folding
 * card per Pattern Type with all its details, read only. The first card
 * starts open.
 *
 * @returns The Pattern Types, or a loading, empty or error state.
 */
export function PatternCatalog() {
  const apiClient = useApiClient();
  const catalogQuery = useQuery({
    queryKey: queryKeys.patternCatalog,
    queryFn: () => apiClient.getPatternCatalog(),
  });
  const patternTypes = catalogQuery.data;

  if (!patternTypes) {
    if (catalogQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load the Pattern Catalog"
          body="Nothing has changed. Pattern Types stay as they were last loaded."
          onRetry={() => void catalogQuery.refetch()}
        />
      );
    }
    return <CardListLoading label="Loading Pattern Types" />;
  }

  if (patternTypes.length === 0) {
    return (
      <EmptyState
        title="No Pattern Types yet"
        body="Pattern Types appear here once their files are loaded on deploy."
      />
    );
  }

  return (
    <>
      <CardList
        items={patternTypes.map((patternType) => ({
          id: patternType.id,
          patternType,
        }))}
        count={
          <CardCount
            count={patternTypes.length}
            words={patternTypes.length === 1 ? "Pattern Type" : "Pattern Types"}
          />
        }
        renderCard={({ id, patternType }, _index, folding) => (
          <PatternTypeCard
            key={id}
            patternType={patternType}
            isOpen={folding.isOpen}
            onToggle={folding.onToggle}
          />
        )}
      />
      <p className="m-0 text-[13px] text-soft">
        <span className="inline-flex items-center gap-1.5 text-[12px] text-text">
          <LockIcon />
          Read only
        </span>{" "}
        Pattern Types live in the repo. Changing one needs a new version and a
        deploy.
      </p>
    </>
  );
}
