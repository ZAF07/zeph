/**
 * An icon button in the text editor's toolbar, with a tooltip naming it and
 * its keyboard shortcut on hover and keyboard focus.
 *
 * @param props - `label` names the action; `shortcut` is how it is written,
 *   like "Ctrl/⌘ B"; `keyShortcuts` is the same for screen readers, like
 *   "Control+B Meta+B"; `iconPath` is the icon's SVG path; `onClick` runs it;
 *   `disabled` greys it out.
 * @returns The button.
 */
export function EditorToolbarButton({
  label,
  shortcut,
  keyShortcuts,
  iconPath,
  onClick,
  disabled = false,
}: {
  label: string;
  shortcut: string;
  keyShortcuts: string;
  iconPath: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        aria-label={label}
        aria-keyshortcuts={keyShortcuts}
        disabled={disabled}
        onMouseDown={(event) => event.preventDefault()}
        onClick={onClick}
        className="inline-flex size-11 cursor-pointer items-center justify-center rounded-input border border-transparent bg-transparent text-soft hover:bg-bg-deep hover:text-cream disabled:cursor-not-allowed disabled:text-mute"
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d={iconPath} />
        </svg>
      </button>
      <span
        aria-hidden="true"
        className="pointer-events-none absolute top-full left-0 z-[300] mt-1.5 hidden rounded-input border border-line bg-bg-deep px-2 py-1 text-[12px] whitespace-nowrap text-text group-hover:block group-has-[:focus-visible]:block"
      >
        {label} <span className="text-soft">{shortcut}</span>
      </span>
    </span>
  );
}
