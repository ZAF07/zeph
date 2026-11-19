"use client";

import Link from "next/link";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { primaryButton } from "@/components/button-styles";
import { CardListFlash, type Flash } from "@/components/CardListFlash";
import { CardTextField } from "@/components/CardTextField";
import { NewCardBox } from "@/components/NewCardBox";
import { ApiError } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

type AddMethod = "set" | "telegram";

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
 * The "Add stickers" box above the Sticker Library list: import a whole
 * sticker set by name, or read how to add stickers in the Admin's own
 * Telegram chat with Zeph.
 *
 * @param props - `onAdded` reloads the library after stickers are added;
 *   `onClose` closes the box.
 * @returns The box with its two tabs.
 */
export function StickerAddBox({
  onAdded,
  onClose,
}: {
  onAdded: () => void;
  onClose: () => void;
}) {
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
    <NewCardBox title="Add stickers" status={null} onCancel={onClose}>
      <div
        role="tablist"
        aria-label="Add method"
        className="flex flex-nowrap gap-x-[22px] overflow-x-auto border-b border-line"
      >
        {addMethods.map((option) => (
          <button
            key={option.id}
            type="button"
            role="tab"
            aria-selected={method === option.id}
            onClick={() => setMethod(option.id)}
            className={`min-h-11 flex-none cursor-pointer border-0 border-b-2 bg-transparent px-0.5 text-[14px] whitespace-nowrap ${
              method === option.id
                ? "border-cream font-normal text-cream"
                : "border-transparent font-light text-soft"
            }`}
          >
            {option.label}
          </button>
        ))}
      </div>

      {method === "set" ? (
        <form onSubmit={importSet} className="flex flex-col gap-[14px]">
          <CardTextField
            label="Sticker set name"
            hint="The part after t.me/addstickers/. Every sticker in the set is added without a note; add notes before Zeph can use them."
            placeholder="e.g. CalmCreatures"
            value={setName}
            onChange={setSetName}
          />
          <button
            type="submit"
            className={`${primaryButton} self-start`}
            disabled={importStickerSet.isPending || setName.trim() === ""}
          >
            {importStickerSet.isPending ? "Importing…" : "Import set"}
          </button>
          <CardListFlash flash={flash} />
        </form>
      ) : (
        <div className="flex flex-col gap-2.5">
          <p className="m-0 text-[14px] text-soft">
            From the Telegram account linked to your Admin account, add stickers
            in your chat with Zeph in one of two ways:
          </p>
          <ul className="m-0 flex list-disc flex-col gap-1.5 pl-5 text-[14px] text-soft">
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
          <p className="m-0 text-[13px] text-soft">
            Refresh this page to see them below as “Needs a note”.
          </p>
          {hasTelegram === false ? (
            <p className="m-0 text-[13px] text-soft">
              Your account has no Telegram yet.{" "}
              <Link href="/connect-telegram" className="text-text underline">
                Connect Telegram
              </Link>{" "}
              first.
            </p>
          ) : null}
        </div>
      )}
    </NewCardBox>
  );
}
