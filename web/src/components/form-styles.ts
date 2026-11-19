/** Class names for form fields, drawn as the card list's text field. */

/** A text input or select. */
export const inputField =
  "box-border min-h-[46px] w-full rounded-input border border-line-strong bg-bg-deep px-3.5 py-[11px] text-[15px] text-text placeholder:text-mute [color-scheme:dark] [&_option]:bg-bg-deep";

/** A label stacked above its field. */
export const fieldLabel = "flex min-w-0 flex-col gap-1.5 text-[13px] text-soft";

/** A small line under a field. */
export const fieldCaption = "m-0 text-[12px] font-normal text-soft";

/** A tall text box for prompts and other long text, in a code font. */
export const codeTextArea = `${inputField} resize-y font-mono text-[13.5px] leading-[1.6]`;
