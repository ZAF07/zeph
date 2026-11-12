import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

/**
 * jsdom does no layout, so text ranges have no boxes; CodeMirror measures
 * them, so give it empty ones.
 */
function emptyRects(): DOMRectList {
  return Object.assign([], { item: () => null }) as unknown as DOMRectList;
}

/** An empty box, for the same reason. */
function emptyRect(): DOMRect {
  return {
    x: 0,
    y: 0,
    width: 0,
    height: 0,
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    toJSON: () => ({}),
  };
}

Range.prototype.getClientRects ??= emptyRects;
Range.prototype.getBoundingClientRect ??= emptyRect;

afterEach(() => {
  cleanup();
});
