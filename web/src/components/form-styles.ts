/** Class names for form fields, drawn as the card list's text field. */

/** A text input or select. */
export const inputField =
  "box-border min-h-[46px] w-full rounded-input border border-line-strong bg-bg-deep px-3.5 py-[11px] text-[15px] text-text placeholder:text-mute [color-scheme:dark] [&_option]:bg-bg-deep";

/**
 * A text input or select inside a list entry, which sits on the deep
 * colour, so the input takes the panel colour to stand out.
 */
export const entryInputField =
  "box-border min-h-[46px] w-full rounded-input border border-line-strong bg-panel px-3.5 py-[11px] text-[15px] text-text placeholder:text-mute [color-scheme:dark] [&_option]:bg-bg-deep";

/** A case's key, in the code font at 14px, as the case form draws it. */
export const keyInputField =
  "box-border min-h-[46px] w-full max-w-[420px] rounded-input border border-line-strong bg-bg-deep px-3.5 py-[11px] font-mono text-[14px] text-text placeholder:text-mute";

/** A label stacked above its field. */
export const fieldLabel = "flex min-w-0 flex-col gap-1.5 text-[13px] text-soft";

/** A small line under a field. */
export const fieldCaption = "m-0 text-[12px] font-normal text-soft";

/** A field's hint under its label: 13px and soft, as every form draws it. */
export const fieldHint = "m-0 text-[13px] text-soft";

/** A tall text box for prompts and other long text, in a code font. */
export const codeTextArea = `${inputField} resize-y font-mono text-[13.5px] leading-[1.6]`;
