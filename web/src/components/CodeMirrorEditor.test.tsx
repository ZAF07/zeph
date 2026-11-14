import { useLayoutEffect } from "react";
import { describe, expect, it } from "vitest";

import { CodeMirrorEditor } from "@/components/CodeMirrorEditor";
import { renderWithQueries } from "@/test/render-with-queries";

/**
 * Records, while the page is being put on screen, whether the editor's
 * labelled text area is already there.
 *
 * @param props - `onCheck` gets whether the editor was found.
 * @returns Nothing visible.
 */
function EditorPresenceCheck({
  onCheck,
}: {
  onCheck: (isEditorThere: boolean) => void;
}) {
  useLayoutEffect(() => {
    onCheck(document.querySelector('[aria-label="Document text"]') !== null);
  });
  return null;
}

describe("CodeMirrorEditor", () => {
  it("is in the page as soon as it is rendered, not a moment later", () => {
    let isEditorThere = false;

    renderWithQueries(
      <>
        <CodeMirrorEditor value="# Mindful breathing" label="Document text" />
        <EditorPresenceCheck
          onCheck={(found) => {
            isEditorThere = found;
          }}
        />
      </>,
    );

    expect(isEditorThere).toBe(true);
  });
});
