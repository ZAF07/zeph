"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { EmptyState } from "@/components/EmptyState";
import { MemoriesPanelHeading } from "@/components/MemoriesPanelHeading";
import { PatternCard } from "@/components/PatternCard";
import { PreferenceSwitch } from "@/components/PreferenceSwitch";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import type { Me, Pattern, ToldPatternState } from "@/lib/api-client";
import { type Copy, readCopy } from "@/lib/copy";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const sectionsInOrder: ToldPatternState[] = [
  "shared",
  "confirmed",
  "contested",
  "closed",
];

/**
 * The Patterns tab: the Patterns Zeph has told the User about, under four
 * headings (being tested, confirmed, ones they disagreed with, and ones
 * that didn't hold up), each with their quotes and what Zeph asked them to
 * notice. Each can be deleted, which also deletes the quotes it rests on.
 * Under the ones they disagreed with is the switch that lets Zeph keep
 * noting evidence for them.
 *
 * @param props - `patterns` are the Patterns Zeph told the User about, in
 *   the order to show them, `me` is the User, `copy` is the Memories
 *   page's Copy with the Account page's switch slots, and `timeZone` is
 *   the User's time zone.
 * @returns The tab's content.
 */
export function PatternsList({
  patterns,
  me,
  copy,
  timeZone,
}: {
  patterns: Pattern[];
  me: Me;
  copy: Copy;
  timeZone?: string;
}) {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();

  const deletePattern = useMutation({
    mutationFn: (patternId: string) => apiClient.deletePattern(patternId),
    onSuccess: (_, patternId) => {
      queryClient.setQueryData(
        queryKeys.patterns,
        patterns.filter((pattern) => pattern.id !== patternId),
      );
      void queryClient.invalidateQueries({ queryKey: queryKeys.keptQuotes });
    },
  });

  const sections = sectionsInOrder
    .map((state) => ({
      state,
      heading: readCopy(copy, `memories.patterns.section.${state}`),
      patterns: patterns.filter((pattern) => pattern.state === state),
    }))
    .filter((section) => section.patterns.length > 0);

  return (
    <>
      <MemoriesPanelHeading
        title={readCopy(copy, "memories.patterns.heading")}
        body={readCopy(copy, "memories.patterns.intro")}
      />

      {deletePattern.isError ? (
        <SaveFailedNote>
          {readCopy(copy, "memories.delete_failed")}
        </SaveFailedNote>
      ) : null}

      {sections.map((section) => (
        <section key={section.state} aria-label={section.heading}>
          <h3 className="mt-0 mb-2 text-[12px] font-medium tracking-[2px] text-soft uppercase">
            {section.heading}
          </h3>
          <div className="flex flex-col gap-3">
            <ul className="m-0 flex list-none flex-col gap-3 p-0">
              {section.patterns.map((pattern) => (
                <li key={pattern.id}>
                  <PatternCard
                    pattern={pattern}
                    copy={copy}
                    timeZone={timeZone}
                    isDeleting={deletePattern.isPending}
                    onDelete={() => deletePattern.mutate(pattern.id)}
                  />
                </li>
              ))}
            </ul>
            {section.state === "contested" ? (
              <PreferenceSwitch
                preference="contested_gathering_enabled"
                title={readCopy(copy, "account.contested_gathering.title")}
                copy={copy}
                enabled={me.contested_gathering_enabled}
                available
                explanation={readCopy(
                  copy,
                  "account.contested_gathering.explanation",
                )}
                changedInChatAt={me.changed_in_chat.contested_gathering}
                timeZone={timeZone}
              />
            ) : null}
          </div>
        </section>
      ))}

      {patterns.length === 0 ? (
        <EmptyState
          title={readCopy(copy, "memories.patterns.empty_title")}
          body={readCopy(copy, "memories.patterns.empty_message")}
        />
      ) : null}
    </>
  );
}
