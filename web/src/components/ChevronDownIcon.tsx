/**
 * The small down chevron drawn in the form template's select box.
 *
 * @param props - `className` places and turns it, such as rotating it to
 *   point right while a group is folded.
 * @returns The icon, hidden from screen readers.
 */
export function ChevronDownIcon({ className }: { className: string }) {
  return (
    <svg
      aria-hidden="true"
      width="12"
      height="8"
      viewBox="0 0 12 8"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      className={className}
    >
      <path d="M1 1.5l5 5 5-5" />
    </svg>
  );
}
