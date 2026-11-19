"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

/**
 * Warns before leaving the page while there are unsaved changes: the
 * browser asks on reload or closing, and following a link is held back
 * until the person says to leave, so the page can ask in its own dialog.
 *
 * @param hasUnsavedChanges - Whether there are changes that would be lost.
 * @returns `leavingTo`, the link held back (null when none); `stay`, which
 *   drops it; and `leave`, which follows it.
 */
export function useUnsavedChangesWarning(hasUnsavedChanges: boolean): {
  leavingTo: string | null;
  stay: () => void;
  leave: () => void;
} {
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
      const link =
        event.target instanceof Element
          ? event.target.closest("a[href]")
          : null;
      const href = link?.getAttribute("href");
      if (href) {
        event.preventDefault();
        event.stopPropagation();
        setLeavingTo(href);
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
