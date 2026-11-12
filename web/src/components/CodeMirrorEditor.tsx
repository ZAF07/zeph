"use client";

import { defaultKeymap, history, historyKeymap } from "@codemirror/commands";
import { markdown } from "@codemirror/lang-markdown";
import { syntaxHighlighting } from "@codemirror/language";
import {
  highlightSelectionMatches,
  openSearchPanel,
  search,
  searchKeymap,
} from "@codemirror/search";
import { Annotation, Compartment, EditorState } from "@codemirror/state";
import {
  drawSelection,
  EditorView,
  highlightActiveLine,
  highlightActiveLineGutter,
  keymap,
  lineNumbers,
} from "@codemirror/view";
import { useEffect, useImperativeHandle, useRef, type Ref } from "react";

import {
  zephEditorTheme,
  zephMarkdownHighlight,
} from "@/components/codemirror-theme";

/** What the toolbar can ask the editor to do. */
export type CodeMirrorEditorHandle = {
  focus: () => void;
  openFind: () => void;
};

const syncedFromValueProp = Annotation.define<boolean>();

/**
 * The editing extensions that change with `readOnly`.
 *
 * @param readOnly - Whether the text can only be read.
 * @returns The extensions.
 */
function readOnlyExtensions(readOnly: boolean) {
  return [
    EditorState.readOnly.of(readOnly),
    EditorView.contentAttributes.of({ "aria-readonly": String(readOnly) }),
  ];
}

/**
 * A CodeMirror 6 Markdown editor: line numbers, soft wrap, Markdown
 * highlighting, active line, find (and replace when editable), undo / redo
 * and Ctrl/⌘+S. When read-only it can still be focused, moved through and
 * searched.
 *
 * @param props - `value` is the text; `onChange` gets each edit; `readOnly`
 *   stops editing; `label` names the editor for screen readers; `onSave`
 *   runs on Ctrl/⌘+S; `ref` gets the commands the toolbar uses.
 * @returns The editor.
 */
export function CodeMirrorEditor({
  value,
  onChange,
  readOnly = false,
  label,
  onSave,
  ref,
}: {
  value: string;
  onChange?: (value: string) => void;
  readOnly?: boolean;
  label: string;
  onSave?: () => void;
  ref?: Ref<CodeMirrorEditorHandle>;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const readOnlyCompartment = useRef(new Compartment());
  const initialValue = useRef(value);
  const initialReadOnly = useRef(readOnly);
  const initialLabel = useRef(label);
  const onChangeRef = useRef(onChange);
  const onSaveRef = useRef(onSave);

  useEffect(() => {
    onChangeRef.current = onChange;
    onSaveRef.current = onSave;
  }, [onChange, onSave]);

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    const view = new EditorView({
      parent: containerRef.current,
      state: EditorState.create({
        doc: initialValue.current,
        extensions: [
          lineNumbers(),
          highlightActiveLineGutter(),
          highlightActiveLine(),
          drawSelection(),
          history(),
          EditorView.lineWrapping,
          markdown(),
          syntaxHighlighting(zephMarkdownHighlight),
          search({ top: true }),
          highlightSelectionMatches(),
          keymap.of([
            {
              key: "Mod-s",
              preventDefault: true,
              run: () => {
                onSaveRef.current?.();
                return true;
              },
            },
            ...searchKeymap,
            ...historyKeymap,
            ...defaultKeymap,
          ]),
          EditorView.contentAttributes.of({
            "aria-label": initialLabel.current,
          }),
          readOnlyCompartment.current.of(
            readOnlyExtensions(initialReadOnly.current),
          ),
          EditorView.updateListener.of((update) => {
            const fromProp = update.transactions.some((transaction) =>
              transaction.annotation(syncedFromValueProp),
            );
            if (update.docChanged && !fromProp) {
              onChangeRef.current?.(update.state.doc.toString());
            }
          }),
          zephEditorTheme,
        ],
      }),
    });
    viewRef.current = view;
    return () => {
      view.destroy();
      viewRef.current = null;
    };
  }, []);

  useEffect(() => {
    const view = viewRef.current;
    if (!view) {
      return;
    }
    const current = view.state.doc.toString();
    if (current !== value) {
      view.dispatch({
        changes: { from: 0, to: current.length, insert: value },
        annotations: syncedFromValueProp.of(true),
      });
    }
  }, [value]);

  useEffect(() => {
    viewRef.current?.dispatch({
      effects: readOnlyCompartment.current.reconfigure(
        readOnlyExtensions(readOnly),
      ),
    });
  }, [readOnly]);

  useImperativeHandle(
    ref,
    () => ({
      focus: () => viewRef.current?.focus(),
      openFind: () => {
        if (viewRef.current) {
          openSearchPanel(viewRef.current);
        }
      },
    }),
    [],
  );

  return <div ref={containerRef} className="h-full min-h-0" />;
}
