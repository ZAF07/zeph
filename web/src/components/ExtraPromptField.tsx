import { EditorLabel } from "@/components/EditorLabel";
import { FormEditor } from "@/components/FormEditor";
import type { ExtraPrompt } from "@/lib/api-client";

/**
 * One extra prompt on a core service: its name and hint above the form
 * template's short editor.
 *
 * @param props - `prompt` is the extra prompt, `savedNote` says when it was
 *   last saved, `value` is its current text and `onChange` is called with
 *   the new text.
 * @returns The name, hint and editor.
 */
export function ExtraPromptField({
  prompt,
  savedNote,
  value,
  onChange,
}: {
  prompt: ExtraPrompt;
  savedNote: string;
  value: string;
  onChange: (text: string) => void;
}) {
  const hintId = `extra-prompt-${prompt.key}-hint`;

  return (
    <div className="flex flex-col gap-3">
      <EditorLabel label={prompt.label} hint={prompt.hint} hintId={hintId} />
      <FormEditor
        label={prompt.label}
        size="short"
        describedById={hintId}
        caption={savedNote}
        value={value}
        onChange={onChange}
      />
    </div>
  );
}
