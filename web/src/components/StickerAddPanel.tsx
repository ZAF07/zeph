"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { fieldCaption, fieldLabel, inputField } from "@/components/form-styles";
import { ApiError } from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

type AddMethod = "set" | "telegram";

type Flash = { text: string; isError: boolean };

const addMethods: { id: AddMethod; label: string }[] = [
  { id: "set", label: "By sticker set name" },
  { id: "telegram", label: "Send from your Telegram" },
];

/**
 * Writes how many stickers an import added.
 *
 * @param count - How many were added.
 * @param setName - The sticker set's name.
 * @returns The message for the Admin.
 */
function importedMessage(count: number, setName: string): string {
  if (count === 0) {
    return `Every sticker in ${setName} is already in the library.`;
  }
  const stickers = count === 1 ? "1 sticker" : `${count} stickers`;
  return `Added ${stickers} from ${setName}. Add notes so Zeph can use them.`;
}

/**
 * The "Add stickers" card: import a whole sticker set by name, or send
 * stickers to Zeph from the Admin's own connected Telegram account.
 *
 * @param props - `onAdded` reloads the library after stickers are added.
 * @returns The card with its two tabs.
 */
export function StickerAddPanel({ onAdded }: { onAdded: () => void }) {
  const apiClient = useApiClient();
  const [method, setMethod] = useState<AddMethod>("set");
  const [setName, setSetName] = useState("");
  const [isImporting, setIsImporting] = useState(false);
  const [flash, setFlash] = useState<Flash | null>(null);
  const [telegramUsername, setTelegramUsername] = useState<
    string | null | undefined
  >(undefined);

  useEffect(() => {
    if (method !== "telegram" || telegramUsername !== undefined) {
      return;
    }
    apiClient
      .getTelegramConnection()
      .then((status) =>
        setTelegramUsername(
          status.connection
            ? (status.connection.telegram_username ?? "")
            : null,
        ),
      )
      .catch(() => setTelegramUsername(null));
  }, [apiClient, method, telegramUsername]);

  async function importSet(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const name = setName.trim();
    setIsImporting(true);
    setFlash(null);
    try {
      const count = await apiClient.importStickerSet(name);
      setFlash({ text: importedMessage(count, name), isError: false });
      setSetName("");
      onAdded();
    } catch (error) {
      setFlash({
        text:
          error instanceof ApiError && error.detail
            ? error.detail
            : "Couldn’t import that set. Please try again.",
        isError: true,
      });
    } finally {
      setIsImporting(false);
    }
  }

  return (
    <section
      aria-labelledby="add-stickers-heading"
      className="flex flex-col rounded-card border border-line bg-white"
    >
      <div className="px-5 pt-4">
        <h2 id="add-stickers-heading" className="m-0 text-[17px] font-semibold">
          Add stickers
        </h2>
      </div>
      <div
        role="tablist"
        aria-label="Add method"
        className="flex gap-1 overflow-x-auto border-b border-line px-3"
      >
        {addMethods.map((option) => (
          <button
            key={option.id}
            type="button"
            role="tab"
            aria-selected={method === option.id}
            onClick={() => setMethod(option.id)}
            className={`-mb-px min-h-12 cursor-pointer whitespace-nowrap border-0 border-b-2 bg-transparent px-4 py-3 text-[15px] ${
              method === option.id
                ? "border-ink font-semibold text-ink"
                : "border-transparent font-medium text-ink-soft"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {method === "set" ? (
        <form
          onSubmit={(event) => void importSet(event)}
          className="flex flex-wrap items-end gap-2.5 px-5 pb-5 pt-4"
        >
          <label className={`${fieldLabel} flex-[1_1_280px]`}>
            Sticker set name
            <input
              type="text"
              value={setName}
              onChange={(event) => setSetName(event.target.value)}
              placeholder="e.g. CalmCreatures"
              className={`${inputField} font-mono`}
            />
          </label>
          <button
            type="submit"
            className={primaryButton}
            disabled={isImporting || setName.trim() === ""}
          >
            {isImporting ? "Importing…" : "Import set"}
          </button>
          <p className={`${fieldCaption} basis-full`}>
            The part after t.me/addstickers/. Every sticker in the set is added
            without a note; add notes before Zeph can use them.
          </p>
          {flash ? (
            <p
              role="status"
              className={`m-0 basis-full rounded-xl px-4 py-3.5 text-sm ${
                flash.isError
                  ? "border border-danger-line bg-danger-tint text-danger-deep"
                  : "bg-blue-tint text-blue-deep"
              }`}
            >
              {flash.text}
            </p>
          ) : null}
        </form>
      ) : (
        <div className="flex flex-col gap-2.5 px-5 pb-5 pt-4">
          <p className="m-0 text-[15px] text-ink-soft">
            From the Telegram account linked to your Admin account, send any
            sticker to Zeph. Refresh this page to see it below as “Needs a
            note”.
          </p>
          {telegramUsername === null ? (
            <p className="m-0 text-caption text-ink-muted">
              Your account has no Telegram yet.{" "}
              <Link href="/connect-telegram">Connect Telegram</Link> first.
            </p>
          ) : null}
          {telegramUsername ? (
            <p
              role="status"
              className="m-0 flex items-center gap-2 text-caption text-ink-muted"
            >
              <span
                aria-hidden="true"
                className="size-2 rounded-full bg-orange-text"
              />
              Listening for stickers from @{telegramUsername}…
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}
