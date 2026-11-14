"use client";

import { secondaryButton } from "@/components/button-styles";
import { DeleteAccountSection } from "@/components/DeleteAccountSection";
import { MemoryNote } from "@/components/MemoryNote";
import { PersonalStickersSection } from "@/components/PersonalStickersSection";
import { PreferenceSwitch } from "@/components/PreferenceSwitch";
import { ProfileForm } from "@/components/ProfileForm";
import { YourDataSection } from "@/components/YourDataSection";
import { useMe, usePlatformContent } from "@/lib/queries";

/**
 * The editable parts of the Account & privacy page: Profile, User Memory,
 * Photo Viewing, Your stickers, Your data and Delete account.
 *
 * @returns The sections, a loading block, or an error with Try again.
 */
export function AccountSettings() {
  const meQuery = useMe();
  const contentQuery = usePlatformContent();
  const me = meQuery.data;
  const content = contentQuery.data;

  if (!me || !content) {
    if (meQuery.isError || contentQuery.isError) {
      return (
        <div
          role="alert"
          className="flex flex-col gap-3.5 rounded-card border border-danger-line bg-danger-tint p-7"
        >
          <h2 className="m-0 text-[17px] font-semibold text-danger-deep">
            We couldn’t load your account
          </h2>
          <p className="m-0 text-[15px] text-ink-soft">
            Nothing has changed. Try again in a moment.
          </p>
          <button
            type="button"
            className={`${secondaryButton} self-start`}
            onClick={() => {
              void meQuery.refetch();
              void contentQuery.refetch();
            }}
          >
            Try again
          </button>
        </div>
      );
    }
    return (
      <div aria-busy="true" className="flex flex-col gap-5">
        <span className="block h-[220px] rounded-card bg-subtle" />
        <span className="block h-[140px] rounded-card bg-subtle" />
        <span className="block h-[240px] rounded-card bg-subtle" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-9">
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
        <MemoryNote note={me.memory_note} />
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
    </div>
  );
}
