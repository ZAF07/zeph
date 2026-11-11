"use client";

import Link from "next/link";
import { QRCodeSVG } from "qrcode.react";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  primaryButton,
  quietButton,
  secondaryButton,
} from "@/components/button-styles";
import type {
  ConnectionToken,
  TelegramConnectionStatus,
} from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

const POLL_INTERVAL_MS = 3000;

/** Which state of the card is on screen. */
type View =
  | { kind: "loading" }
  | { kind: "ready"; token: ConnectionToken }
  | { kind: "waiting"; token: ConnectionToken }
  | { kind: "connected"; telegramUsername: string | null }
  | { kind: "expired" }
  | { kind: "connected_elsewhere" }
  | { kind: "create_failed" };

/**
 * Works out the card state from the backend's status.
 *
 * @param status - The Telegram Connection status from the backend.
 * @param current - The state on screen now, so waiting stays waiting.
 * @returns The new state, or null when a fresh link is needed.
 */
function viewFromStatus(
  status: TelegramConnectionStatus,
  current: View,
): View | null {
  if (status.connection) {
    return {
      kind: "connected",
      telegramUsername: status.connection.telegram_username,
    };
  }
  const token = status.latest_token;
  if (token?.status === "active") {
    return current.kind === "waiting"
      ? { kind: "waiting", token }
      : { kind: "ready", token };
  }
  if (token?.status === "connected_elsewhere") {
    return { kind: "connected_elsewhere" };
  }
  return null;
}

/**
 * Says how long a link has left, rounded up to whole minutes.
 *
 * @param expiresAt - When the link expires, as an ISO timestamp.
 * @returns The minutes left, at least 1.
 */
function minutesLeft(expiresAt: string): number {
  const millisecondsLeft = new Date(expiresAt).getTime() - Date.now();
  return Math.max(1, Math.ceil(millisecondsLeft / 60000));
}

/**
 * The Connect Telegram card. Shows every state of the link: ready (QR code,
 * `/start` code, Open in Telegram), waiting for hello, connected, expired or
 * already used, linked to another account, and couldn't create a link. It
 * checks the backend every few seconds so it updates on its own.
 *
 * @returns The card.
 */
export function TelegramConnectionCard() {
  const apiClient = useApiClient();
  const [view, setView] = useState<View>({ kind: "loading" });
  const viewRef = useRef(view);
  viewRef.current = view;

  const createLink = useCallback(async () => {
    try {
      const token = await apiClient.createConnectionToken();
      setView({ kind: "ready", token });
    } catch {
      setView({ kind: "create_failed" });
    }
  }, [apiClient]);

  const refresh = useCallback(async () => {
    try {
      const status = await apiClient.getTelegramConnection();
      setView(viewFromStatus(status, viewRef.current) ?? { kind: "expired" });
    } catch {
      return;
    }
  }, [apiClient]);

  useEffect(() => {
    async function loadOrCreateLink() {
      try {
        const status = await apiClient.getTelegramConnection();
        const initialView = viewFromStatus(status, { kind: "loading" });
        if (initialView) {
          setView(initialView);
          return;
        }
      } catch {
        setView({ kind: "create_failed" });
        return;
      }
      await createLink();
    }
    void loadOrCreateLink();
  }, [apiClient, createLink]);

  const isPolling = view.kind === "ready" || view.kind === "waiting";
  useEffect(() => {
    if (!isPolling) {
      return;
    }
    const timer = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [isPolling, refresh]);

  if (view.kind === "loading") {
    return (
      <div
        aria-busy="true"
        className="h-[198px] rounded-card border border-line bg-subtle"
      />
    );
  }

  if (view.kind === "ready") {
    const { token } = view;
    return (
      <div className="flex flex-wrap items-center gap-6 rounded-card border border-line bg-white p-6">
        <div
          role="img"
          aria-label="QR code"
          className="flex size-[150px] flex-none items-center justify-center rounded-card border border-line bg-white"
        >
          <QRCodeSVG value={token.deep_link_url} size={126} />
        </div>
        <div className="flex min-w-0 flex-[1_1_220px] flex-col gap-3">
          <a
            href={token.deep_link_url}
            target="_blank"
            rel="noreferrer"
            className={`${primaryButton} self-start`}
            onClick={() => setView({ kind: "waiting", token })}
          >
            Open in Telegram
          </a>
          <p className="m-0 text-sm text-ink-soft">
            Or find{" "}
            <strong className="font-semibold">@{token.bot_username}</strong> and
            send:
          </p>
          <code className="self-start rounded-lg bg-code px-3 py-2 font-mono text-[15px]">
            /start {token.token}
          </code>
          <p className="m-0 text-caption text-ink-muted">
            Works once · expires in {minutesLeft(token.expires_at)} minutes
          </p>
        </div>
      </div>
    );
  }

  if (view.kind === "waiting") {
    const { token } = view;
    return (
      <div
        role="status"
        className="flex flex-col gap-3.5 rounded-card border border-line bg-white p-7"
      >
        <p className="m-0 flex items-center gap-3 text-[17px] font-medium">
          <span
            aria-hidden="true"
            className="size-2.5 rounded-full bg-orange-text"
          />
          Waiting for you to say hello in Telegram…
        </p>
        <p className="m-0 text-[15px] text-ink-soft">
          Once you press Start in Telegram, this page will update on its own.
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={secondaryButton}
            onClick={() => void refresh()}
          >
            I’ve pressed Start
          </button>
          <button
            type="button"
            className={quietButton}
            onClick={() => setView({ kind: "ready", token })}
          >
            Show the code again
          </button>
        </div>
      </div>
    );
  }

  if (view.kind === "connected") {
    return (
      <div
        role="status"
        className="flex flex-col gap-3.5 rounded-card bg-blue-tint p-7"
      >
        <p className="m-0 flex items-center gap-3 text-[19px] font-semibold text-blue-deep">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M5 12l5 5 9-10" />
          </svg>
          Zeph just said hello in Telegram
        </p>
        <p className="m-0 text-[15px] text-blue-deep">
          {view.telegramUsername
            ? `Connected as @${view.telegramUsername}.`
            : "Connected."}{" "}
          Reply whenever you’re ready — there’s no rush.
        </p>
        <Link href="/" className={`${primaryButton} self-start`}>
          Go to your Dashboard
        </Link>
      </div>
    );
  }

  if (view.kind === "expired") {
    return (
      <div
        role="alert"
        className="flex flex-col gap-3.5 rounded-card border border-danger-line bg-danger-tint p-7"
      >
        <p className="m-0 text-[17px] font-semibold text-danger-deep">
          This link has expired or was already used
        </p>
        <p className="m-0 text-[15px] text-ink-soft">
          For your security each link works once and only for a short while. Get
          a fresh one and try again.
        </p>
        <button
          type="button"
          className={`${primaryButton} self-start`}
          onClick={() => void createLink()}
        >
          Get a new link
        </button>
      </div>
    );
  }

  if (view.kind === "connected_elsewhere") {
    return (
      <div
        role="alert"
        className="flex flex-col gap-3.5 rounded-card bg-yellow-tint p-7"
      >
        <p className="m-0 text-[17px] font-semibold text-yellow-deep">
          That Telegram account is linked to another Zeph account
        </p>
        <p className="m-0 text-[15px] text-ink-soft">
          Sign in to that account and disconnect Telegram there first, or use a
          different Telegram account.
        </p>
        <button
          type="button"
          className={`${secondaryButton} self-start`}
          onClick={() => void createLink()}
        >
          Get a new link
        </button>
      </div>
    );
  }

  return (
    <div
      role="alert"
      className="flex flex-col gap-3.5 rounded-card border border-danger-line bg-danger-tint p-7"
    >
      <p className="m-0 text-[17px] font-semibold text-danger-deep">
        We couldn’t create your link
      </p>
      <p className="m-0 text-[15px] text-ink-soft">
        Something went wrong on our side. Please try again in a moment.
      </p>
      <button
        type="button"
        className={`${secondaryButton} self-start`}
        onClick={() => void createLink()}
      >
        Try again
      </button>
    </div>
  );
}
