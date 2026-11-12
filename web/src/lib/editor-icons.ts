import type { MarkdownFormat } from "@/lib/markdown-formatting";

/** SVG paths for the text editor's toolbar icons, on a 24 × 24 grid. */
export const editorIcons = {
  find: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14zM20 20l-4-4",
  undo: "M9 14 4 9l5-5M4 9h10.5a5.5 5.5 0 0 1 0 11H11",
  redo: "m15 14 5-5-5-5M20 9H9.5a5.5 5.5 0 0 0 0 11H13",
};

/** SVG paths for each Markdown format's toolbar icon. */
export const formatIcons: Record<MarkdownFormat, string> = {
  heading: "M6 4v16M18 4v16M6 12h12",
  bold: "M7 4h6a4 4 0 0 1 0 8H7zM7 12h7a4 4 0 0 1 0 8H7z",
  italic: "M19 4h-9M14 20H5M15 4 9 20",
  quote: "M3 21c3 0 7-1 7-8V5H3v8h4M14 21c3 0 7-1 7-8V5h-7v8h4",
  bulletList: "M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01",
  numberedList:
    "M10 6h11M10 12h11M10 18h11M4 6h1v4M4 10h2M6 18H4c0-1 2-2 2-3s-1-1.5-2-1",
};
