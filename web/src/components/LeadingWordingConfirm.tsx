import { CardRemoveConfirm } from "@/components/CardRemoveConfirm";

/**
 * The warning a Thought Experiment's card shows when its wording may lead
 * the User to an answer: each phrase found with what to change, then Keep
 * editing or Save anyway. Drawn as the card list's confirm.
 *
 * @param props - `flags` are the leading phrases, one line each;
 *   `isBusy` turns the buttons off while saving; `onKeep` goes back to
 *   editing; `onSaveAnyway` saves it as it is.
 * @returns The warning.
 */
export function LeadingWordingConfirm({
  flags,
  isBusy,
  onKeep,
  onSaveAnyway,
}: {
  flags: string[];
  isBusy: boolean;
  onKeep: () => void;
  onSaveAnyway: () => void;
}) {
  return (
    <CardRemoveConfirm
      label="Leading wording"
      title="This wording may lead them to an answer"
      body={flags.join(" ")}
      keepLabel="Keep editing"
      confirmLabel="Save anyway"
      isBusy={isBusy}
      onKeep={onKeep}
      onConfirm={onSaveAnyway}
    />
  );
}
