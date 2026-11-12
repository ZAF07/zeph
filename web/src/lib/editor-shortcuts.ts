import type { MarkdownFormat } from "@/lib/markdown-formatting";

/** A text editor keyboard shortcut, as the editor, screen and screen readers write it. */
export type EditorShortcut = {
  key: string;
  label: string;
  ariaKeyShortcuts: string;
};

/** The text editor's undo and redo shortcuts, as CodeMirror's history binds them. */
export const historyShortcuts: Record<"undo" | "redo", EditorShortcut> = {
  undo: {
    key: "Mod-z",
    label: "Ctrl/⌘ Z",
    ariaKeyShortcuts: "Control+Z Meta+Z",
  },
  redo: {
    key: "Mod-Shift-z",
    label: "Ctrl/⌘ Shift Z",
    ariaKeyShortcuts: "Control+Shift+Z Meta+Shift+Z",
  },
};

/** The shortcut for each Markdown format in the text editor. */
export const formatShortcuts: Record<MarkdownFormat, EditorShortcut> = {
  heading: {
    key: "Mod-Alt-2",
    label: "Ctrl/⌘ Alt 2",
    ariaKeyShortcuts: "Control+Alt+2 Meta+Alt+2",
  },
  bold: {
    key: "Mod-b",
    label: "Ctrl/⌘ B",
    ariaKeyShortcuts: "Control+B Meta+B",
  },
  italic: {
    key: "Mod-i",
    label: "Ctrl/⌘ I",
    ariaKeyShortcuts: "Control+I Meta+I",
  },
  quote: {
    key: "Mod-Shift-9",
    label: "Ctrl/⌘ Shift 9",
    ariaKeyShortcuts: "Control+Shift+9 Meta+Shift+9",
  },
  bulletList: {
    key: "Mod-Shift-8",
    label: "Ctrl/⌘ Shift 8",
    ariaKeyShortcuts: "Control+Shift+8 Meta+Shift+8",
  },
  numberedList: {
    key: "Mod-Shift-7",
    label: "Ctrl/⌘ Shift 7",
    ariaKeyShortcuts: "Control+Shift+7 Meta+Shift+7",
  },
};
