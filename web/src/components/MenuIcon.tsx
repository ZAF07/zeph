/**
 * One of the menu's 20px line icons, drawn in the link's text colour.
 *
 * @param props - `path` is the icon's SVG path.
 * @returns The icon, hidden from screen readers.
 */
export function MenuIcon({ path }: { path: string }) {
  return (
    <svg
      aria-hidden="true"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="flex-none"
    >
      <path d={path} />
    </svg>
  );
}
