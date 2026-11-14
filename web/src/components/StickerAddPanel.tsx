"use client";

import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { fieldCaption, fieldLabel, inputField } from "@/components/form-styles";
import { ApiError } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
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
 * The "Add stickers" card: import a whole sticker set by name, or read how
 * to add stickers in the Admin's own Telegram chat with Zeph.
 *
 * @param props - `onAdded` reloads the library after stickers are added.
 * @returns The card with its two tabs.
 */
export function StickerAddPanel({ onAdded }: { onAdded: () => void }) {
  const apiClient = useApiClient();
  const [method, setMethod] = useState<AddMethod>("set");
  const [setName, setSetName] = useState("");
  const [flash, setFlash] = useState<Flash | null>(null);

  const telegramQuery = useQuery({
    queryKey: queryKeys.telegramConnection,
    queryFn: () => apiClient.getTelegramConnection(),
    enabled: method === "telegram",
  });
  const hasTelegram = telegramQuery.isError
    ? false
    : telegramQuery.data && telegramQuery.data.connection !== null;

  const importStickerSet = useMutation({
    mutationFn: (name: string) => apiClient.importStickerSet(name),
    onMutate: () => setFlash(null),
    onSuccess: (count, name) => {
      setFlash({ text: importedMessage(count, name), isError: false });
      setSetName("");
      onAdded();
    },
    onError: (error) =>
      setFlash({
        text:
          error instanceof ApiError && error.detail
            ? error.detail
            : "Couldn’t import that set. Please try again.",
        isError: true,
      }),
  });

  function importSet(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    importStickerSet.mutate(setName.trim());
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
          onSubmit={importSet}
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
            disabled={importStickerSet.isPending || setName.trim() === ""}
          >
            {importStickerSet.isPending ? "Importing…" : "Import set"}
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
            From the Telegram account linked to your Admin account, add stickers
            in your chat with Zeph in one of two ways:
          </p>
          <ul className="m-0 flex list-disc flex-col gap-1.5 pl-5 text-[15px] text-ink-soft">
            <li>
              Tell Zeph you want to add stickers, as single stickers or whole
              sets, then send them. Each one gets a 👍. Send any message that
              isn’t a sticker when you’re done, and Zeph says what it added.
            </li>
            <li>
              Reply “add this” to a sticker in the chat, or “add this set” for
              its whole set.
            </li>
          </ul>
          <p className="m-0 text-caption text-ink-muted">
            Refresh this page to see them below as “Needs a note”.
          </p>
          {hasTelegram === false ? (
            <p className="m-0 text-caption text-ink-muted">
              Your account has no Telegram yet.{" "}
              <Link href="/connect-telegram">Connect Telegram</Link> first.
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}
