import Link from "next/link";

/**
 * The sticky top bar that replaces the sidebar below 900px: the wordmark and
 * the menu button, whose icon becomes a cross while the menu is open.
 *
 * @param props - `menuId` is the menu panel's id; `menuOpen` says whether it is open; `onMenuToggle` opens or closes it.
 * @returns The top bar.
 */
export function PhoneBar({
  menuId,
  menuOpen,
  onMenuToggle,
}: {
  menuId: string;
  menuOpen: boolean;
  onMenuToggle: () => void;
}) {
  return (
    <header className="sticky top-0 z-[5] box-border flex items-center justify-between gap-3 border-b border-line bg-bg-deep py-2 pr-2.5 pl-5 min-[900px]:hidden">
      <Link
        href="/"
        className="text-[24px] font-normal text-cream no-underline"
      >
        Zeph
      </Link>
      <button
        type="button"
        aria-label={menuOpen ? "Close the menu" : "Open the menu"}
        aria-expanded={menuOpen}
        aria-controls={menuId}
        onClick={onMenuToggle}
        className="flex size-11 flex-none cursor-pointer items-center justify-center rounded-input border-0 bg-transparent text-text"
      >
        <svg
          aria-hidden="true"
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        >
          <path
            d={menuOpen ? "M6 6l12 12M18 6L6 18" : "M4 7h16M4 12h16M4 17h16"}
          />
        </svg>
      </button>
    </header>
  );
}
