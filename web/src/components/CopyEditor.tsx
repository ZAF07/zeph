"use client";

import { useEffect, useState } from "react";

import { CardSaveBar } from "@/components/CardSaveBar";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { CopySearchResults } from "@/components/CopySearchResults";
import { copySlotFieldId, CopySlotField } from "@/components/CopySlotField";
import { CopyTabs } from "@/components/CopyTabs";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { SavedNote } from "@/components/SavedNote";
import { SearchField } from "@/components/SearchField";
import { ApiError } from "@/lib/api-client";
import type { Copy } from "@/lib/copy";
import { type CopySearchMatch, searchCopySlots } from "@/lib/copy-search";
import { copySlotRows } from "@/lib/copy-slot-rows";
import { saveFailedMessage } from "@/lib/save-failed-message";
import { useCopyPage, useSaveCopyTab } from "@/lib/use-copy-page";
import { useUnsavedChangesWarning } from "@/lib/use-unsaved-changes-warning";

/** Where a tab switch is going: the tab, and the slot to land on, if any. */
type TabSwitch = { tab: string; slotKey: string | null };

/**
 * Scrolls a Copy slot's editor into view and puts the cursor in it.
 *
 * @param slotKey - The slot's key.
 */
function bringSlotIntoView(slotKey: string) {
  const field = document.getElementById(copySlotFieldId(slotKey));
  field?.scrollIntoView({ block: "center" });
  field?.querySelector("textarea")?.focus({ preventScroll: true });
}

/**
 * The Copy page's editor: a tab per website page, the chosen tab's slots in
 * page order (a "one" and "many" pair side by side) and one save bar that
 * saves the tab's changes together. A save the backend turns away shows
 * each reason on its slot. A search finds
 * slots in every tab by their text and takes the Admin to the one picked.
 * Switching tabs or leaving the page with unsaved edits asks first.
 *
 * @returns The editor, or a loading panel or error with Try again.
 */
export function CopyEditor() {
  const pageQuery = useCopyPage();
  const saveTab = useSaveCopyTab();
  const [selectedTab, setSelectedTab] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Copy>({});
  const [switchingTo, setSwitchingTo] = useState<TabSwitch | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [landingSlot, setLandingSlot] = useState<string | null>(null);
  const tabs = pageQuery.data;
  const tab = tabs?.find((found) => found.tab === selectedTab) ?? tabs?.[0];
  const changedTexts: Copy = Object.fromEntries(
    (tab?.slots ?? [])
      .filter((slot) => (drafts[slot.key] ?? slot.text) !== slot.text)
      .map((slot) => [slot.key, drafts[slot.key] ?? slot.text]),
  );
  const isDirty = Object.keys(changedTexts).length > 0;
  const leaving = useUnsavedChangesWarning(isDirty);

  useEffect(() => {
    if (landingSlot !== null) {
      bringSlotIntoView(landingSlot);
      setLandingSlot(null);
    }
  }, [landingSlot]);

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

  if (!tab) {
    return null;
  }

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

  function landOn(slotKey: string) {
    setSearchQuery("");
    setLandingSlot(slotKey);
  }

  function switchTab({ tab: tabKey, slotKey }: TabSwitch) {
    setSwitchingTo(null);
    setSelectedTab(tabKey);
    discard();
    if (slotKey !== null) {
      landOn(slotKey);
    }
  }

  function requestSwitch(target: TabSwitch) {
    if (isDirty) {
      setSwitchingTo(target);
    } else {
      switchTab(target);
    }
  }

  function chooseTab(tabKey: string) {
    if (tabKey !== tab?.tab) {
      requestSwitch({ tab: tabKey, slotKey: null });
    }
  }

  function pickMatch(match: CopySearchMatch) {
    const matchTabKey = match.tab.tab;
    if (matchTabKey === tab?.tab) {
      landOn(match.slot.key);
    } else {
      requestSwitch({ tab: matchTabKey, slotKey: match.slot.key });
    }
  }

  function save(tabKey: string) {
    saveTab.mutate(
      { tab: tabKey, texts: changedTexts },
      { onSuccess: () => setDrafts({}) },
    );
  }

  return (
    <>
      <SearchField
        label="Search all tabs"
        placeholder="Search all tabs by text"
        value={searchQuery}
        onChange={setSearchQuery}
      />
      {searchQuery.trim() ? (
        <CopySearchResults
          matches={searchCopySlots(tabs, searchQuery)}
          onPick={pickMatch}
        />
      ) : null}
      <CopyTabs tabs={tabs} selected={tab.tab} onSelect={chooseTab} />
      <section
        role="tabpanel"
        aria-label={tab.name}
        className="flex flex-col gap-3"
      >
        {copySlotRows(tab.slots).map((row) => (
          <div
            key={row[0].key}
            className="grid gap-3 min-[900px]:auto-cols-fr min-[900px]:grid-flow-col"
          >
            {row.map((slot) => (
              <CopySlotField
                key={slot.key}
                slot={slot}
                value={drafts[slot.key] ?? slot.text}
                error={slotErrors[slot.key]}
                onChange={(text) => edit(slot.key, text)}
              />
            ))}
          </div>
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
      {switchingTo !== null ? (
        <ConfirmDialog
          open
          title="Switch tabs and lose your changes?"
          body="Your edits on this tab since the last save aren’t kept."
          cancelLabel="Keep editing"
          confirmLabel="Switch tab"
          onConfirm={() => switchTab(switchingTo)}
          onCancel={() => setSwitchingTo(null)}
        />
      ) : null}
      {leaving.leavingTo !== null ? (
        <ConfirmDialog
          open
          title="Leave and lose your changes?"
          body="Your edits on this tab since the last save aren’t kept."
          cancelLabel="Keep editing"
          confirmLabel="Leave"
          onConfirm={leaving.leave}
          onCancel={leaving.stay}
        />
      ) : null}
    </>
  );
}
