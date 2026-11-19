import { FormEditor } from "@/components/FormEditor";
import type { ExtraPrompt } from "@/lib/api-client";

/**
 * One extra prompt on a core service, in the form template's short editor,
 * with its name and, when it has one, a hint saying when it's used along
 * the top.
 *
 * @param props - `prompt` is the extra prompt, `value` its current text and
 *   `onChange` is called with the new text.
 * @returns The editor.
 */
export function ExtraPromptField({
  prompt,
  value,
  onChange,
}: {
  prompt: ExtraPrompt;
  value: string;
  onChange: (text: string) => void;
}) {
  const hintId = `extra-prompt-${prompt.key}-hint`;

  return (
    <FormEditor
      label={prompt.label}
      size="short"
      describedById={prompt.hint ? hintId : undefined}
      caption={
        <>
          <span className="text-text">{prompt.label}</span>
          {prompt.hint ? (
            <>
              {" · "}
              <span id={hintId}>{prompt.hint}</span>
            </>
          ) : null}
        </>
      }
      value={value}
      onChange={onChange}
    />
  );
}
