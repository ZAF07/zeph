"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { ArchivedMemoryCategoryCard } from "@/components/ArchivedMemoryCategoryCard";
import { CardCount } from "@/components/CardCount";
import { CardList } from "@/components/CardList";
import { CardListFlash, type Flash } from "@/components/CardListFlash";
import { CardListLoading } from "@/components/CardListLoading";
import { EmptyState } from "@/components/EmptyState";
import { LoadFailed } from "@/components/LoadFailed";
import { MemoryCategoryCard } from "@/components/MemoryCategoryCard";
import { NewMemoryCategoryBox } from "@/components/NewMemoryCategoryBox";
import {
  ApiError,
  type MemoryCategoryInput,
  type MemoryCategoryOverview,
} from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The admin Memory Categories manager, from the card-list template: a
 * folding card per active category to change its name, description and
 * "always include", or archive it; then the archived ones, each with
 * Restore; and a box above the list to add one. There is no delete.
 *
 * @returns The lists, or a loading, empty or error state.
 */
export function MemoryCategoriesManager() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const [isAdding, setIsAdding] = useState(false);
  const [flash, setFlash] = useState<Flash | null>(null);

  const categoriesQuery = useQuery({
    queryKey: queryKeys.memoryCategories,
    queryFn: () => apiClient.listMemoryCategories(),
  });
  const categories = categoriesQuery.data;

  async function reloadCategories() {
    void queryClient.invalidateQueries({ queryKey: queryKeys.memoryGroups });
    void queryClient.invalidateQueries({ queryKey: queryKeys.home });
    await queryClient.invalidateQueries({
      queryKey: queryKeys.memoryCategories,
    });
  }

  const change = useMutation({
    mutationFn: async ({
      action,
    }: {
      target: MemoryCategoryOverview;
      action: () => Promise<unknown>;
      successText: string | null;
    }) => {
      await action();
      await reloadCategories();
    },
    onMutate: () => setFlash(null),
    onSuccess: (_, { successText }) => {
      if (successText) {
        setFlash({ text: successText, isError: false });
      }
    },
    onError: (error, { target }) =>
      setFlash({
        text:
          error instanceof ApiError && error.status === 409 && error.detail
            ? error.detail
            : `Couldn’t change ${target.name}. Please try again.`,
        isError: true,
      }),
  });
  const changingId = change.isPending ? change.variables.target.id : null;

  async function add(input: MemoryCategoryInput) {
    await apiClient.addMemoryCategory(input);
    setIsAdding(false);
    setFlash({ text: `Added ${input.name.trim()}.`, isError: false });
    await reloadCategories();
  }

  async function save(
    category: MemoryCategoryOverview,
    input: MemoryCategoryInput,
  ) {
    await apiClient.updateMemoryCategory(category.id, input);
    setFlash({ text: `Saved ${input.name.trim()}.`, isError: false });
    await reloadCategories();
  }

  if (!categories) {
    if (categoriesQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Memory Categories"
          body="Zeph keeps using the last saved set."
          onRetry={() => void categoriesQuery.refetch()}
        />
      );
    }
    return <CardListLoading label="Loading categories" />;
  }

  const active = categories.filter((category) => !category.archived);
  const archived = categories.filter((category) => category.archived);

  return (
    <>
      <CardList
        items={active}
        count={
          <CardCount
            count={active.length}
            words={
              active.length === 1 ? "active category" : "active categories"
            }
          />
        }
        addLabel="Add category"
        onAdd={() => {
          setIsAdding(true);
          setFlash(null);
        }}
        isAddDisabled={isAdding}
        aboveList={
          <>
            <CardListFlash flash={flash} />
            {isAdding ? (
              <NewMemoryCategoryBox
                onAdd={add}
                onCancel={() => setIsAdding(false)}
              />
            ) : null}
            {categories.length === 0 && !isAdding ? (
              <EmptyState
                title="No categories yet"
                body="Zeph needs at least one active category to save memories. Suggested starters: Life details, Relationships, Goals, Values & beliefs, Challenges, Preferences, What helps."
              />
            ) : null}
          </>
        }
        renderCard={(category, _index, folding) => (
          <MemoryCategoryCard
            key={category.id}
            category={category}
            isOpen={folding.isOpen}
            onToggle={folding.onToggle}
            onSave={(input) => save(category, input)}
            onAlwaysIncludeChange={(alwaysInclude) =>
              change.mutate({
                target: category,
                action: () =>
                  apiClient.updateMemoryCategory(category.id, {
                    name: category.name,
                    description: category.description,
                    always_include: alwaysInclude,
                  }),
                successText: null,
              })
            }
            onArchive={() =>
              change.mutate({
                target: category,
                action: () => apiClient.archiveMemoryCategory(category.id),
                successText: `Archived ${category.name}. Its memories are kept.`,
              })
            }
            isChanging={changingId === category.id}
          />
        )}
      />
      {archived.length > 0 ? (
        <CardList
          items={archived}
          count={<CardCount count={archived.length} words="archived" />}
          startsFolded
          renderCard={(category, _index, folding) => (
            <ArchivedMemoryCategoryCard
              key={category.id}
              category={category}
              isOpen={folding.isOpen}
              onToggle={folding.onToggle}
              onRestore={() =>
                change.mutate({
                  target: category,
                  action: () => apiClient.restoreMemoryCategory(category.id),
                  successText: `Restored ${category.name}.`,
                })
              }
              isChanging={changingId === category.id}
            />
          )}
        />
      ) : null}
    </>
  );
}
