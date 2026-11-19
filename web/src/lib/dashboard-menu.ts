/**
 * A User page in the Dashboard menu, as `design/reference/Dashboard.html`
 * lists it. Its label is Copy, in the Shared tab.
 */
export type UserMenuItem = {
  labelCopyKey: string;
  href: string;
  iconPath: string;
  toBuild?: boolean;
};

/**
 * An admin page in the Dashboard menu, as `design/reference/Admin.html`
 * lists it. Admin pages' own words are not Copy.
 */
export type AdminMenuItem = {
  label: string;
  href: string;
  toBuild?: boolean;
};

/** The User pages, in the order the menu shows them. */
export const userMenuItems: UserMenuItem[] = [
  {
    labelCopyKey: "shared.dashboard.home",
    href: "/",
    iconPath: "M4 10.5L12 4l8 6.5V20H4zM10 20v-5h4v5",
  },
  {
    labelCopyKey: "shared.dashboard.memories",
    href: "/memories",
    iconPath: "M12 3v4M12 17v4M3 12h4M17 12h4M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8",
  },
  {
    labelCopyKey: "shared.dashboard.check_ins",
    href: "/check-ins",
    iconPath: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18M12 7v5l3 2",
  },
  {
    labelCopyKey: "shared.dashboard.account",
    href: "/account",
    iconPath: "M12 3l8 3v6c0 4.5-3.4 8.2-8 9-4.6-.8-8-4.5-8-9V6z",
  },
  {
    labelCopyKey: "shared.dashboard.plan",
    href: "/plan",
    iconPath: "M4 7h16v10H4zM4 11h16",
    toBuild: true,
  },
];

/** The admin pages, in the order the menu's Admin section shows them. */
export const adminMenuItems: AdminMenuItem[] = [
  { label: "Overview", href: "/admin", toBuild: true },
  { label: "Users", href: "/admin/users" },
  { label: "Persona", href: "/admin/persona" },
  { label: "Prompts & models", href: "/admin/prompts" },
  { label: "Safety", href: "/admin/safety" },
  { label: "Safeguard Events", href: "/admin/safeguard-events" },
  { label: "Knowledge", href: "/admin/knowledge" },
  { label: "Memory Categories", href: "/admin/memory-categories" },
  { label: "Needs", href: "/admin/needs" },
  { label: "Moves", href: "/admin/moves" },
  { label: "Check-in Kinds", href: "/admin/check-in-kinds" },
  { label: "Check-in log", href: "/admin/check-in-log" },
  { label: "Check-in Schedule", href: "/admin/check-in-schedule" },
  { label: "Sticker Library", href: "/admin/stickers" },
  { label: "Features", href: "/admin/features" },
  { label: "Platform settings", href: "/admin/settings" },
  { label: "Copy", href: "/admin/copy" },
  { label: "Usage", href: "/admin/usage" },
  { label: "Model call log", href: "/admin/model-calls" },
  { label: "Evals", href: "/admin/evals" },
  { label: "Plans", href: "/admin/plans", toBuild: true },
];

/**
 * Says whether a User menu item is the page being viewed.
 *
 * @param href - The item's address.
 * @param pathname - The address of the page being viewed.
 * @returns True when the item should be marked as the current page.
 */
export function isUserItemCurrent(href: string, pathname: string): boolean {
  return href === pathname;
}

/**
 * Says whether an admin menu item is the page being viewed. An item stays
 * marked on the pages under it, like a Knowledge document's page, except
 * Overview, which every admin page sits under.
 *
 * @param href - The item's address.
 * @param pathname - The address of the page being viewed.
 * @returns True when the item should be marked as the current page.
 */
export function isAdminItemCurrent(href: string, pathname: string): boolean {
  if (href === pathname) {
    return true;
  }
  return href !== "/admin" && pathname.startsWith(`${href}/`);
}
