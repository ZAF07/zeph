"use client";

import { useState } from "react";

import { CardSaveBar } from "@/components/CardSaveBar";
import { CopySlotField } from "@/components/CopySlotField";
import { CopyTabs } from "@/components/CopyTabs";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { SavedNote } from "@/components/SavedNote";
import { ApiError } from "@/lib/api-client";
import type { Copy } from "@/lib/copy";
import { saveFailedMessage } from "@/lib/save-failed-message";
import { useCopyPage, useSaveCopyTab } from "@/lib/use-copy-page";

/**
 * The Copy page's editor: a tab per website page, the chosen tab's slots in
 * page order and one save bar that saves the tab's changes together. A save
 * the backend turns away shows each reason on its slot.
 *
 * @returns The editor, or a loading panel or error with Try again.
 */
export function CopyEditor() {
  const pageQuery = useCopyPage();
  const saveTab = useSaveCopyTab();
  const [selectedTab, setSelectedTab] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Copy>({});
  const tabs = pageQuery.data;

  if (!tabs) {
    if (pageQuery.isError) {
      return (
        <LoadFailed
          title="Couldn’t load Copy"
          body="The website keeps showing the last saved words."
          onRetry={() => void pageQuery.refetch()}
        />
      );
    }
    return <LoadingPanel shape="card" label="Loading Copy" />;
  }

  const tab = tabs.find((found) => found.tab === selectedTab) ?? tabs[0];
  if (!tab) {
    return null;
  }

  const changedTexts: Copy = Object.fromEntries(
    tab.slots
      .filter((slot) => (drafts[slot.key] ?? slot.text) !== slot.text)
      .map((slot) => [slot.key, drafts[slot.key] ?? slot.text]),
  );
  const isDirty = Object.keys(changedTexts).length > 0;
  const slotErrors =
    saveTab.error instanceof ApiError ? saveTab.error.fields : {};

  function edit(key: string, text: string) {
    setDrafts({ ...drafts, [key]: text });
    saveTab.reset();
  }

  function discard() {
    setDrafts({});
    saveTab.reset();
  }

  function save(tabKey: string) {
    saveTab.mutate(
      { tab: tabKey, texts: changedTexts },
      { onSuccess: () => setDrafts({}) },
    );
  }

  return (
    <>
      <CopyTabs
        tabs={tabs}
        selected={tab.tab}
        onSelect={(tabKey) => {
          setSelectedTab(tabKey);
          discard();
        }}
      />
      <section
        role="tabpanel"
        aria-label={tab.name}
        className="flex flex-col gap-3"
      >
        {tab.slots.map((slot) => (
          <CopySlotField
            key={slot.key}
            slot={slot}
            value={drafts[slot.key] ?? slot.text}
            error={slotErrors[slot.key]}
            onChange={(text) => edit(slot.key, text)}
          />
        ))}
        <CardSaveBar
          note="Changes show on the next page load."
          failedMessage={saveFailedMessage(saveTab.error)}
          isDirty={isDirty}
          canSave={isDirty}
          isBusy={saveTab.isPending}
          onDiscard={discard}
          onSave={() => save(tab.tab)}
        />
      </section>
      {saveTab.isSuccess ? (
        <SavedNote>Saved. It shows on the next page load.</SavedNote>
      ) : null}
    </>
  );
}
