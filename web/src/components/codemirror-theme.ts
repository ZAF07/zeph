import { HighlightStyle } from "@codemirror/language";
import { EditorView } from "@codemirror/view";
import { tags } from "@lezer/highlight";

/**
 * Reads a Zeph design token, with its value as a fallback.
 *
 * @param name - The token's name, like "line" for `--color-line`.
 * @param fallback - Its value on the Foundations screen.
 * @returns A CSS colour.
 */
function color(name: string, fallback: string): string {
  return `var(--color-${name}, ${fallback})`;
}

const ink = color("ink", "#0a0a0a");
const inkSoft = color("ink-soft", "#525252");
const inkMuted = color("ink-muted", "#6b6b6b");
const line = color("line", "#ebebeb");
const lineStrong = color("line-strong", "#d4d4d4");
const subtle = color("subtle", "#fafafa");
const code = color("code", "#f4f4f5");
const blue = color("blue", "#1f4fff");
const blueTint = color("blue-tint", "#edf1ff");
const blueDeep = color("blue-deep", "#1533b3");
const yellow = color("yellow", "#ffc633");
const yellowTint = color("yellow-tint", "#fff6cc");
const orangeText = color("orange-text", "#c2410c");

/** The editor's look, in Zeph's colours and type. */
export const zephEditorTheme = EditorView.theme({
  "&": {
    height: "100%",
    backgroundColor: "#ffffff",
    color: ink,
    fontSize: "14px",
  },
  "&.cm-focused": { outline: "none" },
  ".cm-scroller": {
    fontFamily: "var(--font-mono, ui-monospace, monospace)",
    lineHeight: "1.7",
    overflow: "auto",
  },
  ".cm-content": { padding: "16px 0", caretColor: blue },
  ".cm-line": { padding: "0 20px 0 14px" },
  ".cm-gutters": {
    backgroundColor: subtle,
    color: inkMuted,
    borderRight: `1px solid ${line}`,
  },
  ".cm-lineNumbers .cm-gutterElement": { padding: "0 10px 0 14px" },
  ".cm-activeLine": { backgroundColor: "rgba(31, 79, 255, 0.04)" },
  ".cm-activeLineGutter": { backgroundColor: blueTint, color: blueDeep },
  ".cm-cursor": { borderLeftColor: blue, borderLeftWidth: "2px" },
  "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, ::selection":
    { backgroundColor: "#d6e0ff" },
  ".cm-searchMatch": {
    backgroundColor: yellowTint,
    outline: `1px solid ${yellow}`,
    borderRadius: "2px",
  },
  ".cm-searchMatch.cm-searchMatch-selected": { backgroundColor: yellow },
  ".cm-panels": {
    backgroundColor: subtle,
    color: ink,
  },
  ".cm-panels.cm-panels-top": { borderBottom: `1px solid ${line}` },
  ".cm-panel.cm-search": {
    display: "flex",
    flexWrap: "wrap",
    alignItems: "center",
    gap: "8px",
    padding: "10px 44px 10px 12px",
    fontFamily: "var(--font-sans, system-ui, sans-serif)",
    fontSize: "13px",
  },
  ".cm-panel.cm-search br": { flexBasis: "100%", height: 0 },
  ".cm-panel.cm-search label": {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    color: inkSoft,
  },
  ".cm-panel.cm-search [name=close]": {
    top: "10px",
    right: "12px",
    width: "28px",
    height: "28px",
    borderRadius: "999px",
    fontSize: "18px",
    color: inkSoft,
    cursor: "pointer",
  },
  ".cm-textfield": {
    minHeight: "34px",
    minWidth: "min(220px, 100%)",
    margin: 0,
    padding: "6px 10px",
    border: `1px solid ${lineStrong}`,
    borderRadius: "8px",
    backgroundColor: "#ffffff",
    fontSize: "14px",
  },
  ".cm-button": {
    minHeight: "34px",
    margin: 0,
    padding: "6px 12px",
    border: `1px solid ${lineStrong}`,
    borderRadius: "999px",
    backgroundImage: "none",
    backgroundColor: "#ffffff",
    color: ink,
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    textTransform: "capitalize",
  },
  ".cm-button:active": { backgroundImage: "none", backgroundColor: blueTint },
});

/** How Markdown is coloured in the editor. */
export const zephMarkdownHighlight = HighlightStyle.define([
  { tag: tags.heading, fontWeight: "600", color: ink },
  { tag: tags.heading1, fontWeight: "700" },
  { tag: tags.strong, fontWeight: "700" },
  { tag: tags.emphasis, fontStyle: "italic" },
  { tag: tags.quote, color: inkSoft, fontStyle: "italic" },
  { tag: tags.list, color: orangeText },
  { tag: [tags.link, tags.url], color: blue },
  { tag: tags.monospace, backgroundColor: code, borderRadius: "3px" },
  { tag: [tags.processingInstruction, tags.meta], color: inkMuted },
  { tag: tags.contentSeparator, color: inkMuted },
]);
