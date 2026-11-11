"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import type { TelegramConnectionStatus } from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

type LoadState =
  | { kind: "loading" }
  | { kind: "loaded"; status: TelegramConnectionStatus }
  | { kind: "failed" };

/**
 * Shows whether the User's Telegram Connection is made, with a Connect
 * Telegram button when it isn't.
 *
 * @returns The status card.
 */
export function TelegramStatusCard() {
  const apiClient = useApiClient();
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  const load = useCallback(async () => {
    try {
      const status = await apiClient.getTelegramConnection();
      setState({ kind: "loaded", status });
    } catch {
      setState({ kind: "failed" });
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  if (state.kind === "loading") {
    return (
      <div
        aria-busy="true"
        className="h-[120px] rounded-card border border-line bg-subtle"
      />
    );
  }

  if (state.kind === "failed") {
    return (
      <div
        role="alert"
        className="flex flex-wrap items-center justify-between gap-3 rounded-card border border-danger-line bg-danger-tint p-4 text-danger-deep"
      >
        <span className="text-sm">
          We couldn’t load this. Nothing you’ve shared is lost.
        </span>
        <button
          type="button"
          className={`${secondaryButton} bg-white`}
          onClick={() => void load()}
        >
          Try again
        </button>
      </div>
    );
  }

  const { connection } = state.status;
  if (connection) {
    return (
      <p className="m-0 rounded-xl bg-blue-tint px-4 py-3.5 text-sm text-blue-deep">
        {connection.telegram_username
          ? `Telegram connected as @${connection.telegram_username}.`
          : "Telegram connected."}
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3.5 rounded-card border border-line bg-white p-7">
      <h3 className="m-0 text-h3 font-semibold">Connect Telegram</h3>
      <p className="m-0 text-[15px] text-ink-soft">
        You talk to Zeph in Telegram. Connect your account to say hello.
      </p>
      <Link href="/connect-telegram" className={`${primaryButton} self-start`}>
        Connect Telegram
      </Link>
    </div>
  );
}
