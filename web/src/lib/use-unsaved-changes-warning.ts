"use client";

import { useEffect } from "react";

/**
 * Warns before leaving the page while there are unsaved changes: the
 * browser asks on reload or closing, and following a link asks first.
 *
 * @param hasUnsavedChanges - Whether there are changes that would be lost.
 * @param message - What to ask before following a link.
 */
export function useUnsavedChangesWarning(
  hasUnsavedChanges: boolean,
  message: string,
): void {
  useEffect(() => {
    if (!hasUnsavedChanges) {
      return;
    }
    function warnBeforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault();
    }
    function confirmLinkClick(event: MouseEvent) {
      const link =
        event.target instanceof Element
          ? event.target.closest("a[href]")
          : null;
      if (link && !window.confirm(message)) {
        event.preventDefault();
        event.stopPropagation();
      }
    }
    window.addEventListener("beforeunload", warnBeforeUnload);
    document.addEventListener("click", confirmLinkClick, true);
    return () => {
      window.removeEventListener("beforeunload", warnBeforeUnload);
      document.removeEventListener("click", confirmLinkClick, true);
    };
  }, [hasUnsavedChanges, message]);
}
