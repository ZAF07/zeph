"use client";

import { AttentionCard } from "@/components/AttentionCard";
import { primaryButton, secondaryButton } from "@/components/button-styles";
import { ConfirmDialog } from "@/components/ConfirmDialog";
import { EmptyState } from "@/components/EmptyState";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { PausedNotice } from "@/components/PausedNotice";
import { PillLink } from "@/components/PillLink";
import { SavedNote } from "@/components/SavedNote";
import { SaveFailedNote } from "@/components/SaveFailedNote";
import { StatesSheetSample } from "@/components/StatesSheetSample";
import { StatesSheetSection } from "@/components/StatesSheetSection";

/** The confirm dialogs the design lists, and the page each one is on. */
const confirmPlaces = [
  { action: "Delete all memories", page: "Memories" },
  { action: "Delete my data", page: "Account & privacy" },
  { action: "Delete my account", page: "Account & privacy" },
  { action: "Cancel plan", page: "Plan" },
];

/** Does nothing: the sheet's buttons are samples. */
function doNothing(): void {}

/**
 * The design's `States` sheet, drawn with the shared state parts so it can be
 * checked against `design/baseline/States.png`. Design-fixture mode only.
 *
 * @returns The sheet.
 */
export function StatesSheet() {
  return (
    <div className="mx-auto flex max-w-[1160px] flex-col gap-[52px] px-8 pt-11 pb-16">
      <div>
        <div className="text-[26px] font-normal text-cream">Zeph</div>
        <h1 className="mt-[14px] mb-[6px] text-[32px] leading-[1.15] font-normal text-cream">
          States
        </h1>
        <p className="m-0 max-w-[640px] text-[14px] text-soft">
          What each page shows when there is nothing yet, while it loads, when
          something fails, and before anything is deleted. Every page uses these
          same parts.
        </p>
      </div>

      <StatesSheetSection
        eyebrow="Nothing yet"
        title="Empty"
        lead="A dashed outline, one plain sentence, and the next step if there is one. No illustration."
      >
        <StatesSheetSample label="Home, before Telegram is connected">
          <AttentionCard
            title="Zeph can’t reach you yet."
            body="Conversations and check-ins happen in Telegram. Linking takes one tap."
            action={
              <PillLink
                href="/connect-telegram"
                label="Connect Telegram"
                primary
              />
            }
          />
        </StatesSheetSample>
        <StatesSheetSample label="Memories, nothing remembered">
          <EmptyState
            title="Nothing remembered yet"
            body="As you talk with Zeph, the details that matter will appear here. You can delete any of them."
            action={<PillLink href="#" label="Talk to Zeph" />}
          />
        </StatesSheetSample>
        <StatesSheetSample label="Patterns, none confirmed">
          <EmptyState
            title="No patterns yet"
            body="When Zeph notices the same thing across different parts of your life, and you agree with it, it appears here with what it is based on."
          />
        </StatesSheetSample>
        <StatesSheetSample label="Check-ins, none sent">
          <EmptyState
            title="No check-ins yet"
            body="When Zeph checks in, you’ll see it here with whether you replied."
          />
        </StatesSheetSample>
        <StatesSheetSample label="Memories, switched off">
          <PausedNotice
            title="Memory is off"
            body="Zeph isn’t keeping new details. What it already remembers stays until you delete it."
            action={
              <button type="button" className={secondaryButton}>
                Turn memory on
              </button>
            }
          />
        </StatesSheetSample>
        <StatesSheetSample label="Check-ins, paused">
          <PausedNotice
            title="Check-ins are paused until 25 Nov"
            body="Zeph won’t message first until then. Everything else stays as it is."
            action={
              <button type="button" className={secondaryButton}>
                Resume now
              </button>
            }
          />
        </StatesSheetSample>
      </StatesSheetSection>

      <StatesSheetSection
        eyebrow="While it loads"
        title="Loading"
        lead="Soft bars in the shape of what is coming, inside the same panel. No spinners, and nothing jumps when the content arrives."
      >
        <StatesSheetSample label="A banner">
          <LoadingPanel shape="banner" label="Loading" />
        </StatesSheetSample>
        <StatesSheetSample label="A card or list">
          <LoadingPanel shape="card" label="Loading memories" />
        </StatesSheetSample>
      </StatesSheetSection>

      <StatesSheetSection
        eyebrow="When something fails"
        title="Errors"
        lead="Say what failed in plain words, keep what the person typed, and always offer one way forward."
      >
        <StatesSheetSample label="A page or card could not load">
          <LoadFailed
            title="Couldn’t load your memories"
            body="Check your connection and try again. Nothing has been lost."
            onRetry={doNothing}
          />
        </StatesSheetSample>
        <StatesSheetSample label="A change could not be saved">
          <SaveFailedNote>
            Couldn’t save your check-in settings. They are as you left them. Try
            again.
          </SaveFailedNote>
        </StatesSheetSample>
        <StatesSheetSample label="A change was saved">
          <SavedNote>Saved.</SavedNote>
        </StatesSheetSample>
        <StatesSheetSample label="A button while it works">
          <div className="flex flex-wrap gap-2">
            <button type="button" className={primaryButton} disabled>
              Saving…
            </button>
            <button type="button" className={primaryButton}>
              Save changes
            </button>
          </div>
        </StatesSheetSample>
      </StatesSheetSection>

      <StatesSheetSection
        eyebrow="Before deleting"
        title="Confirm"
        lead="Only for things that can’t be undone. The safe choice comes first and the dialog names exactly what will go."
      >
        <StatesSheetSample label="Delete all memories" wide>
          <ConfirmDialog
            open
            modal={false}
            title="Delete all memories?"
            body="Zeph will forget every memory it holds about you. Conversation Summaries and your account stay. This can’t be undone."
            cancelLabel="Keep them"
            confirmLabel="Delete all memories"
            onConfirm={doNothing}
            onCancel={doNothing}
          />
        </StatesSheetSample>
        <StatesSheetSample label="Where this applies">
          <div className="rounded-card border border-line bg-panel px-[22px] py-1.5">
            {confirmPlaces.map((place, index) => (
              <div
                key={place.action}
                className={`box-content flex min-h-11 flex-wrap items-center justify-between gap-x-4 gap-y-1 ${index > 0 ? "border-t border-line" : ""}`}
              >
                <span className="text-[14px] text-soft">{place.action}</span>
                <span className="text-[14px] text-text">{place.page}</span>
              </div>
            ))}
          </div>
        </StatesSheetSample>
      </StatesSheetSection>
    </div>
  );
}
