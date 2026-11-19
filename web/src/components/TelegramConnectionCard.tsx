"use client";

import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { QRCodeSVG } from "qrcode.react";
import { Fragment, useCallback, useEffect, useRef, useState } from "react";

import { primaryButton, secondaryButton } from "@/components/button-styles";
import { panelCard } from "@/components/card-styles";
import { LoadFailed } from "@/components/LoadFailed";
import { LoadingPanel } from "@/components/LoadingPanel";
import { TelegramStateCard } from "@/components/TelegramStateCard";
import type {
  ConnectionToken,
  TelegramConnectionStatus,
} from "@/lib/api-client";
import {
  type Copy,
  fillPlaceholderParts,
  fillPlaceholders,
  readCopy,
} from "@/lib/copy";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

const POLL_INTERVAL_MS = 3000;

/** The Copy slot names for each state where the link can't be used. */
const linkProblemSlots = {
  expired: { title: "expired_title", body: "expired_body" },
  connected_elsewhere: { title: "elsewhere_title", body: "elsewhere_body" },
};

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
 * hidden on a phone where the button is the action, `/start` code, Open in
 * Telegram), waiting for hello, connected, expired or
 * already used, linked to another account, and couldn't create a link. It
 * checks the backend every few seconds so it updates on its own, and once
 * connected Home loads again so it shows the connection. Its words are the
 * Connect Telegram tab's `connect_telegram.card.*` Copy slots.
 *
 * @param props - `copy` holds the card's Copy slots; `compact` draws the ready state as the small card on the
 *   onboarding Telegram step: QR code, Open in Telegram and the expiry,
 *   without the `/start` code.
 * @returns The card.
 */
export function TelegramConnectionCard({
  copy,
  compact = false,
}: {
  copy: Copy;
  compact?: boolean;
}) {
  const cardCopy = (slot: string) =>
    readCopy(copy, `connect_telegram.card.${slot}`);
  const expiryText = (token: ConnectionToken) => {
    const minutes = minutesLeft(token.expires_at);
    return fillPlaceholders(
      cardCopy(minutes === 1 ? "expires_one" : "expires_many"),
      { minutes },
    );
  };
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
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

  const isConnected = view.kind === "connected";
  useEffect(() => {
    if (isConnected) {
      void queryClient.invalidateQueries({ queryKey: queryKeys.home });
    }
  }, [isConnected, queryClient]);

  const isPolling = view.kind === "ready" || view.kind === "waiting";
  useEffect(() => {
    if (!isPolling) {
      return;
    }
    const timer = setInterval(() => void refresh(), POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  }, [isPolling, refresh]);

  if (view.kind === "loading") {
    return <LoadingPanel shape="card" label={cardCopy("loading")} />;
  }

  if (view.kind === "ready" && compact) {
    const { token } = view;
    return (
      <div className="box-border flex flex-col gap-3 rounded-tile border border-line bg-panel px-5 py-[18px]">
        <div className="flex flex-wrap items-center gap-x-7 gap-y-5">
          <div
            role="img"
            aria-label={cardCopy("qr_label")}
            className="flex size-[126px] flex-none items-center justify-center rounded-note bg-cream text-ink max-[899px]:hidden"
          >
            <QRCodeSVG
              value={token.deep_link_url}
              size={102}
              bgColor="transparent"
              fgColor="currentColor"
            />
          </div>
          <div className="flex flex-[1_1_220px] flex-col items-start gap-2.5">
            <a
              href={token.deep_link_url}
              target="_blank"
              rel="noreferrer"
              className={primaryButton}
              onClick={() => setView({ kind: "waiting", token })}
            >
              {cardCopy("open_button")}{" "}
              <span aria-hidden="true" className="ml-2.5">
                →
              </span>
            </a>
            <span className="text-[12px] text-soft">{expiryText(token)}</span>
          </div>
        </div>
      </div>
    );
  }

  if (view.kind === "ready") {
    const { token } = view;
    return (
      <div className={panelCard}>
        <div className="flex flex-wrap items-center gap-x-8 gap-y-6">
          <div
            role="img"
            aria-label={cardCopy("qr_label")}
            className="box-border flex size-[150px] flex-none items-center justify-center rounded-note bg-cream text-ink max-[899px]:hidden"
          >
            <QRCodeSVG
              value={token.deep_link_url}
              size={126}
              bgColor="transparent"
              fgColor="currentColor"
            />
          </div>
          <div className="flex min-w-0 flex-[1_1_260px] flex-col items-start gap-3">
            <a
              href={token.deep_link_url}
              target="_blank"
              rel="noreferrer"
              className={primaryButton}
              onClick={() => setView({ kind: "waiting", token })}
            >
              {cardCopy("open_button")}{" "}
              <span aria-hidden="true" className="ml-2.5">
                →
              </span>
            </a>
            <p className="m-0 text-[14px] text-soft">
              {fillPlaceholderParts(cardCopy("message_bot"), {
                bot: (
                  <span className="font-normal text-text">
                    @{token.bot_username}
                  </span>
                ),
              }).map((piece, index) => (
                <Fragment key={index}>{piece}</Fragment>
              ))}
            </p>
            <code className="rounded-input border border-line bg-bg-deep px-3.5 py-2 font-[monospace] text-[15px] text-text">
              /start {token.token}
            </code>
            <span className="text-[12px] text-soft">{expiryText(token)}</span>
          </div>
        </div>
      </div>
    );
  }

  if (view.kind === "waiting") {
    const { token } = view;
    return (
      <TelegramStateCard
        role="status"
        title={cardCopy("waiting_title")}
        body={cardCopy("waiting_body")}
        actions={
          <>
            <button
              type="button"
              className={primaryButton}
              onClick={() => void refresh()}
            >
              {cardCopy("pressed_start")}
            </button>
            <button
              type="button"
              className={secondaryButton}
              onClick={() => setView({ kind: "ready", token })}
            >
              {cardCopy("show_code")}
            </button>
          </>
        }
      />
    );
  }

  if (view.kind === "connected") {
    const connectedAs = view.telegramUsername
      ? fillPlaceholders(cardCopy("connected_as"), {
          username: view.telegramUsername,
        })
      : cardCopy("connected_no_username");
    return (
      <TelegramStateCard
        role="status"
        title={cardCopy("connected_title")}
        body={`${connectedAs} ${cardCopy("connected_body")}`}
        actions={
          <Link href="/" className={primaryButton}>
            {cardCopy("dashboard_link")}
          </Link>
        }
      />
    );
  }

  if (view.kind === "expired" || view.kind === "connected_elsewhere") {
    const slots = linkProblemSlots[view.kind];
    return (
      <TelegramStateCard
        role="alert"
        isProblem
        title={cardCopy(slots.title)}
        body={cardCopy(slots.body)}
        actions={
          <button
            type="button"
            className={primaryButton}
            onClick={() => void createLink()}
          >
            {cardCopy("new_link")}
          </button>
        }
      />
    );
  }

  return (
    <LoadFailed
      title={cardCopy("create_failed_title")}
      body={cardCopy("create_failed_body")}
      retryLabel={cardCopy("create_failed_retry")}
      onRetry={() => void createLink()}
    />
  );
}
