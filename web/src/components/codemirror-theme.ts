import { HighlightStyle } from "@codemirror/language";
import { EditorView } from "@codemirror/view";
import { tags } from "@lezer/highlight";

/**
 * Reads a Zeph design token, with its value as a fallback.
 *
 * @param name - The token's name, like "line" for `--color-line`.
 * @param fallback - Its value in `design/tokens.css`.
 * @returns A CSS colour.
 */
function color(name: string, fallback: string): string {
  return `var(--color-${name}, ${fallback})`;
}

const text = color("text", "#eaf2f3");
const soft = color("soft", "#bdd0d5");
const mute = color("mute", "#9db6be");
const cream = color("cream", "#f3e8d6");
const ink = color("ink", "#0b2a3c");
const line = color("line", "#2a5263");
const lineStrong = color("line-strong", "#5b8b96");
const bgDeep = color("bg-deep", "#071922");
const zeph = color("zeph", "#2a5c66");
const orange = color("orange", "#f0a050");

/**
 * A token's colour, see-through, for a soft fill.
 *
 * @param token - The colour, from `color`.
 * @param percent - How much of it shows, from 0 to 100.
 * @returns A CSS colour.
 */
function faint(token: string, percent: number): string {
  return `color-mix(in srgb, ${token} ${percent}%, transparent)`;
}

/** The editor's look, in Zeph's colours and type. */
export const zephEditorTheme = EditorView.theme({
  "&": {
    height: "100%",
    backgroundColor: "transparent",
    color: text,
    fontSize: "14px",
  },
  "&.cm-focused": { outline: "none" },
  ".cm-scroller": {
    fontFamily: "var(--font-mono, ui-monospace, monospace)",
    lineHeight: "1.7",
    overflow: "auto",
  },
  ".cm-content": { padding: "16px 0", caretColor: cream },
  ".cm-line": { padding: "0 20px 0 14px" },
  ".cm-gutters": {
    backgroundColor: bgDeep,
    color: mute,
    borderRight: `1px solid ${line}`,
  },
  ".cm-lineNumbers .cm-gutterElement": { padding: "0 10px 0 14px" },
  ".cm-activeLine": { backgroundColor: faint(zeph, 25) },
  ".cm-activeLineGutter": { backgroundColor: faint(zeph, 40), color: text },
  ".cm-cursor": { borderLeftColor: cream, borderLeftWidth: "2px" },
  "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, ::selection":
    { backgroundColor: zeph },
  ".cm-searchMatch": {
    backgroundColor: faint(orange, 25),
    outline: `1px solid ${orange}`,
    borderRadius: "2px",
  },
  ".cm-searchMatch.cm-searchMatch-selected": {
    backgroundColor: orange,
    color: ink,
  },
  ".cm-panels": {
    backgroundColor: bgDeep,
    color: text,
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
    color: soft,
  },
  ".cm-panel.cm-search [name=close]": {
    top: "10px",
    right: "12px",
    width: "28px",
    height: "28px",
    borderRadius: "999px",
    fontSize: "18px",
    color: soft,
    cursor: "pointer",
  },
  ".cm-textfield": {
    minHeight: "34px",
    minWidth: "min(220px, 100%)",
    margin: 0,
    padding: "6px 10px",
    border: `1px solid ${lineStrong}`,
    borderRadius: "10px",
    backgroundColor: bgDeep,
    color: text,
    fontSize: "14px",
  },
  ".cm-button": {
    minHeight: "34px",
    margin: 0,
    padding: "6px 12px",
    border: `1px solid ${lineStrong}`,
    borderRadius: "999px",
    backgroundImage: "none",
    backgroundColor: "transparent",
    color: text,
    fontSize: "13px",
    fontWeight: 500,
    cursor: "pointer",
    textTransform: "capitalize",
  },
  ".cm-button:active": { backgroundImage: "none", backgroundColor: zeph },
});

/** How Markdown is coloured in the editor. */
export const zephMarkdownHighlight = HighlightStyle.define([
  { tag: tags.heading, fontWeight: "400", color: cream },
  { tag: tags.strong, fontWeight: "500", color: cream },
  { tag: tags.emphasis, fontStyle: "italic" },
  { tag: tags.quote, color: soft, fontStyle: "italic" },
  { tag: tags.list, color: soft },
  { tag: [tags.link, tags.url], color: soft, textDecoration: "underline" },
  { tag: tags.monospace, backgroundColor: bgDeep, borderRadius: "3px" },
  { tag: [tags.processingInstruction, tags.meta], color: mute },
  { tag: tags.contentSeparator, color: mute },
]);
