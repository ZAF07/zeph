/**
 * A small padlock, shown beside "No message content" notes.
 *
 * @returns The icon.
 */
export function LockIcon() {
  return (
    <svg
      width="12"
      height="14"
      viewBox="0 0 12 14"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.3"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <rect x="1.5" y="6" width="9" height="7" rx="1.5" />
      <path d="M3.5 6V4a2.5 2.5 0 0 1 5 0v2" />
    </svg>
  );
}
