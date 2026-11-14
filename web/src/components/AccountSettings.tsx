"use client";

import { useCallback, useEffect, useState } from "react";

import { secondaryButton } from "@/components/button-styles";
import { DeleteAccountSection } from "@/components/DeleteAccountSection";
import { PersonalStickersSection } from "@/components/PersonalStickersSection";
import { PhotoViewingSetting } from "@/components/PhotoViewingSetting";
import { ProfileForm } from "@/components/ProfileForm";
import { UserMemorySetting } from "@/components/UserMemorySetting";
import { YourDataSection } from "@/components/YourDataSection";
import type { Me, PlatformContent } from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "failed" }
  | { kind: "loaded"; me: Me; content: PlatformContent };

/**
 * The editable parts of the Account & privacy page: Profile, User Memory,
 * Photo Viewing, Your stickers, Your data and Delete account.
 *
 * @returns The sections, a loading block, or an error with Try again.
 */
export function AccountSettings() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      const [me, content] = await Promise.all([
        apiClient.getMe(),
        apiClient.getPlatformContent(),
      ]);
      setState({ kind: "loaded", me, content });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  if (state.kind === "loading") {
    return (
      <div aria-busy="true" className="flex flex-col gap-5">
        <span className="block h-[220px] rounded-card bg-subtle" />
        <span className="block h-[140px] rounded-card bg-subtle" />
        <span className="block h-[240px] rounded-card bg-subtle" />
      </div>
    );
  }

  if (state.kind === "failed") {
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
          onClick={() => void load()}
        >
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-9">
      <ProfileForm me={state.me} />
      <UserMemorySetting
        enabled={state.me.user_memory_enabled}
        available={state.me.user_memory_available}
        explanation={state.content.user_memory_explanation}
        note={state.me.memory_note}
        changedInChatAt={state.me.changed_in_chat.user_memory}
        timeZone={state.me.time_zone ?? undefined}
      />
      <PhotoViewingSetting
        enabled={state.me.photo_viewing_enabled}
        available={state.me.photo_viewing_available}
        explanation={state.content.photo_viewing_explanation}
        changedInChatAt={state.me.changed_in_chat.photo_viewing}
        timeZone={state.me.time_zone ?? undefined}
      />
      <PersonalStickersSection
        available={state.me.personal_stickers_available}
      />
      <YourDataSection retentionDays={state.content.message_retention_days} />
      <DeleteAccountSection />
    </div>
  );
}
