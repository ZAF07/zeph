"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

/** What the page shows while a link is held back, and the two ways out. */
export type LeaveWarning = {
  leavingTo: string | null;
  stay: () => void;
  leave: () => void;
};

/**
 * Says which in-app page a click would open in this tab, if any. Clicks
 * that open a new tab, download, jump within the page or leave the site
 * are left to the browser.
 *
 * @param event - The click.
 * @returns The link's path, or null when the click isn't a plain in-app
 *   link.
 */
function inAppLinkPath(event: MouseEvent): string | null {
  if (
    event.defaultPrevented ||
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey
  ) {
    return null;
  }
  const link =
    event.target instanceof Element ? event.target.closest("a[href]") : null;
  if (
    !(link instanceof HTMLAnchorElement) ||
    link.target !== "" ||
    link.hasAttribute("download")
  ) {
    return null;
  }
  const url = new URL(link.href);
  const isSamePage =
    url.pathname === window.location.pathname &&
    url.search === window.location.search;
  if (url.origin !== window.location.origin || (isSamePage && url.hash)) {
    return null;
  }
  return `${url.pathname}${url.search}${url.hash}`;
}

/**
 * Warns before leaving the page while there are unsaved changes: the
 * browser asks on reload or closing, and following a link is held back
 * until the person says to leave, so the page can ask in its own dialog.
 *
 * @param hasUnsavedChanges - Whether there are changes that would be lost.
 * @returns `leavingTo`, the link held back (null when none); `stay`, which
 *   drops it; and `leave`, which follows it.
 */
export function useUnsavedChangesWarning(
  hasUnsavedChanges: boolean,
): LeaveWarning {
  const router = useRouter();
  const [leavingTo, setLeavingTo] = useState<string | null>(null);

  useEffect(() => {
    if (!hasUnsavedChanges) {
      return;
    }
    function warnBeforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault();
    }
    function holdLinkClick(event: MouseEvent) {
      const path = inAppLinkPath(event);
      if (path !== null) {
        event.preventDefault();
        event.stopPropagation();
        setLeavingTo(path);
      }
    }
    window.addEventListener("beforeunload", warnBeforeUnload);
    document.addEventListener("click", holdLinkClick, true);
    return () => {
      window.removeEventListener("beforeunload", warnBeforeUnload);
      document.removeEventListener("click", holdLinkClick, true);
    };
  }, [hasUnsavedChanges]);

  return {
    leavingTo,
    stay: () => setLeavingTo(null),
    leave: () => {
      if (leavingTo !== null) {
        setLeavingTo(null);
        router.push(leavingTo);
      }
    },
  };
}
