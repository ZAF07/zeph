import { fieldCaption, fieldLabel, inputField } from "@/components/form-styles";
import type { ExtraPrompt } from "@/lib/api-client";

/**
 * A text box for one extra prompt on a core service's card, with its label
 * and, when it has one, a hint under the label saying when it's used.
 *
 * @param props - `prompt` is the extra prompt, `value` its current text and
 *   `onChange` is called with the new text.
 * @returns The field.
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
  const fieldId = `extra-prompt-${prompt.key}`;
  const hintId = `${fieldId}-hint`;

  return (
    <div className={fieldLabel}>
      <span className="flex flex-col gap-0.5">
        <label htmlFor={fieldId}>{prompt.label}</label>
        {prompt.hint ? (
          <span id={hintId} className={fieldCaption}>
            {prompt.hint}
          </span>
        ) : null}
      </span>
      <textarea
        id={fieldId}
        className={`${inputField} resize-y font-mono text-[13.5px] leading-relaxed`}
        rows={4}
        aria-describedby={prompt.hint ? hintId : undefined}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  );
}
