/**
 * The name of a text editor and its hint, drawn above the editor box as in
 * the form template.
 *
 * @param props - `label` names the text; `hint` says what it is, what it
 *   serves and which step reads it; `hintId` is the hint's id, so the
 *   editor can point to it.
 * @returns The name and hint.
 */
export function EditorLabel({
  label,
  hint,
  hintId,
}: {
  label: string;
  hint: string;
  hintId: string;
}) {
  return (
    <div>
      <div className="text-[15px] font-normal text-text">{label}</div>
      <div id={hintId} className="max-w-[640px] text-[13px] text-soft">
        {hint}
      </div>
    </div>
  );
}
