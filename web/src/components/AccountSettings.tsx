"use client";

import { DeleteAccountSection } from "@/components/DeleteAccountSection";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { MemoryOffNotice } from "@/components/MemoryOffNotice";
import { PersonalStickersSection } from "@/components/PersonalStickersSection";
import { PreferenceSwitch } from "@/components/PreferenceSwitch";
import { ProfileForm } from "@/components/ProfileForm";
import { YourDataSection } from "@/components/YourDataSection";
import { type Copy, readCopy } from "@/lib/copy";
import { useMe, usePlatformContent } from "@/lib/queries";

/**
 * The editable parts of the Account & privacy page: Profile, User Memory,
 * Photo Viewing, Your stickers, Delete my data and Delete account. Every
 * word is the Account tab's Copy, with the location labels from
 * Onboarding's, except the explanations and the Delete my data description,
 * which are still Platform Settings.
 *
 * @param props - `copy` holds the Account page's Copy slots and
 *   onboarding's location labels.
 * @returns The sections, a loading panel, or an error with Try again.
 */
export function AccountSettings({ copy }: { copy: Copy }) {
  const accountCopy = (slot: string) => readCopy(copy, `account.${slot}`);
  const meQuery = useMe();
  const contentQuery = usePlatformContent();
  const me = meQuery.data;
  const content = contentQuery.data;

  if (!me || !content) {
    if (meQuery.isError || contentQuery.isError) {
      return (
        <LoadFailed
          title={accountCopy("load_failed.title")}
          body={accountCopy("load_failed.body")}
          retryLabel={accountCopy("load_failed.retry")}
          onRetry={() => {
            void meQuery.refetch();
            void contentQuery.refetch();
          }}
        />
      );
    }
    return <LoadingPanel shape="card" label={accountCopy("loading")} />;
  }

  return (
    <>
      <ProfileForm me={me} copy={copy} />
      <PreferenceSwitch
        preference="user_memory_enabled"
        title={accountCopy("memory.title")}
        copy={copy}
        enabled={me.user_memory_enabled}
        available={me.user_memory_available}
        explanation={content.user_memory_explanation}
        changedInChatAt={me.changed_in_chat.user_memory}
        timeZone={me.time_zone ?? undefined}
      >
        {me.memory_note ? (
          <MemoryOffNotice note={me.memory_note} canTurnOn={false} />
        ) : null}
      </PreferenceSwitch>
      <PreferenceSwitch
        preference="photo_viewing_enabled"
        title={accountCopy("photos.title")}
        copy={copy}
        enabled={me.photo_viewing_enabled}
        available={me.photo_viewing_available}
        explanation={content.photo_viewing_explanation}
        changedInChatAt={me.changed_in_chat.photo_viewing}
        timeZone={me.time_zone ?? undefined}
      />
      <PersonalStickersSection
        available={me.personal_stickers_available}
        copy={copy}
      />
      <YourDataSection
        retentionDays={content.message_retention_days}
        deleteMyDataDescription={content.delete_my_data_description}
        copy={copy}
      />
      <DeleteAccountSection copy={copy} />
    </>
  );
}
