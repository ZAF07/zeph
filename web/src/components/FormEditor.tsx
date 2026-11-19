import type { ReactNode } from "react";

/** How tall the text box is at least: Persona's tall box, or a short one. */
const minHeightClass = {
  tall: "min-h-[300px]",
  short: "min-h-[120px]",
};

/**
 * The form template's editor: a box with a caption and the character count
 * along the top, the text in a code font that grows with what is typed, and
 * room for a save bar at its foot.
 *
 * @param props - `label` names the text for screen readers; `caption` is
 *   the line at the top left, such as when it was last saved; `value` is the
 *   text and `onChange` gets the new text; `size` picks the tall or short
 *   box; `maxLength`, when given, shows in the count as the most characters
 *   allowed; `describedById` is the id of a hint about the text, if any;
 *   `children` goes at the foot, usually the save bar.
 * @returns The editor box.
 */
export function FormEditor({
  label,
  caption,
  value,
  onChange,
  size = "tall",
  maxLength,
  describedById,
  children,
}: {
  label: string;
  caption: ReactNode;
  value: string;
  onChange: (value: string) => void;
  size?: "tall" | "short";
  maxLength?: number;
  describedById?: string;
  children?: ReactNode;
}) {
  return (
    <div className="rounded-card border border-line bg-panel">
      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-line px-5 py-3 text-[12px] text-soft">
        <span>{caption}</span>
        <span className="font-mono">
          {maxLength === undefined
            ? `${value.length} characters`
            : `${value.length} / ${maxLength} characters`}
        </span>
      </div>
      <textarea
        aria-label={label}
        aria-describedby={describedById}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={`m-0 box-border block w-full resize-y border-0 bg-transparent p-5 font-mono text-[13.5px] leading-[1.6] whitespace-pre-wrap text-text field-sizing-content ${minHeightClass[size]}`}
      />
      {children}
    </div>
  );
}
