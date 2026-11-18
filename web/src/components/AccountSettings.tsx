"use client";

import { DeleteAccountSection } from "@/components/DeleteAccountSection";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { MemoryOffNotice } from "@/components/MemoryOffNotice";
import { PersonalStickersSection } from "@/components/PersonalStickersSection";
import { PreferenceSwitch } from "@/components/PreferenceSwitch";
import { ProfileForm } from "@/components/ProfileForm";
import { YourDataSection } from "@/components/YourDataSection";
import { useMe, usePlatformContent } from "@/lib/queries";

/** Does nothing: the switch beside the memory-off notice turns memory on. */
function doNothing(): void {}

/**
 * The editable parts of the Account & privacy page: Profile, User Memory,
 * Photo Viewing, Your stickers, Delete my data and Delete account.
 *
 * @returns The sections, a loading panel, or an error with Try again.
 */
export function AccountSettings() {
  const meQuery = useMe();
  const contentQuery = usePlatformContent();
  const me = meQuery.data;
  const content = contentQuery.data;

  if (!me || !content) {
    if (meQuery.isError || contentQuery.isError) {
      return (
        <LoadFailed
          title="We couldn’t load your account"
          body="Nothing has changed. Try again in a moment."
          onRetry={() => {
            void meQuery.refetch();
            void contentQuery.refetch();
          }}
        />
      );
    }
    return <LoadingPanel shape="card" label="Loading your account" />;
  }

  return (
    <>
      <ProfileForm me={me} />
      <PreferenceSwitch
        preference="user_memory_enabled"
        title="Remember meaningful details"
        enabled={me.user_memory_enabled}
        available={me.user_memory_available}
        explanation={content.user_memory_explanation}
        changedInChatAt={me.changed_in_chat.user_memory}
        timeZone={me.time_zone ?? undefined}
      >
        {me.memory_note ? (
          <MemoryOffNotice
            note={me.memory_note}
            canTurnOn={false}
            isSaving={false}
            onTurnOn={doNothing}
          />
        ) : null}
      </PreferenceSwitch>
      <PreferenceSwitch
        preference="photo_viewing_enabled"
        title="Look at my photos"
        enabled={me.photo_viewing_enabled}
        available={me.photo_viewing_available}
        explanation={content.photo_viewing_explanation}
        changedInChatAt={me.changed_in_chat.photo_viewing}
        timeZone={me.time_zone ?? undefined}
      />
      <PersonalStickersSection available={me.personal_stickers_available} />
      <YourDataSection
        retentionDays={content.message_retention_days}
        deleteMyDataDescription={content.delete_my_data_description}
      />
      <DeleteAccountSection />
    </>
  );
}
