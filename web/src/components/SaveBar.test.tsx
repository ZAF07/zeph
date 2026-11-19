import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { SaveBar } from "@/components/SaveBar";

const failedMessage = "Couldn’t save. Your text is still here.";

/**
 * Renders the save bar with the given state and spy handlers.
 *
 * @param state - The parts of the bar's state that differ per test.
 * @returns The Discard and Save spies.
 */
function renderSaveBar(state: {
  isDirty: boolean;
  isSaving?: boolean;
  failedMessage?: string | null;
  canSave?: boolean;
  placement?: "inside" | "alone";
}) {
  const onDiscard = vi.fn();
  const onSave = vi.fn();
  render(
    <SaveBar
      isDirty={state.isDirty}
      isSaving={state.isSaving ?? false}
      failedMessage={state.failedMessage ?? null}
      canSave={state.canSave ?? state.isDirty}
      saveLabel="Save Persona"
      placement={state.placement ?? "alone"}
      onDiscard={onDiscard}
      onSave={onSave}
    />,
  );
  return { onDiscard, onSave };
}

describe("SaveBar", () => {
  it("draws 'Nothing changed': the note and both buttons in the off look", () => {
    renderSaveBar({ isDirty: false });

    const note = screen.getByText(
      "Changes apply to the next message after saving.",
    );
    expect(note).toHaveClass("text-[13px]", "text-soft");
    for (const name of ["Discard", "Save Persona"]) {
      const button = screen.getByRole("button", { name });
      expect(button).toBeDisabled();
      expect(button).toHaveClass(
        "disabled:border-line-strong",
        "disabled:bg-transparent",
        "disabled:text-mute",
      );
    }
    expect(screen.queryByText("Unsaved changes")).toBeNull();
  });

  it("draws 'Unsaved changes': the orange tag, Discard and the cream Save", async () => {
    const user = userEvent.setup();
    const { onDiscard, onSave } = renderSaveBar({ isDirty: true });

    expect(screen.getByText("Unsaved changes")).toHaveClass(
      "rounded-pill",
      "border-orange",
      "px-3",
      "py-[3px]",
      "text-[12px]",
      "text-orange",
    );
    const discard = screen.getByRole("button", { name: "Discard" });
    const save = screen.getByRole("button", { name: "Save Persona" });
    expect(discard).toHaveClass("border-soft", "text-text");
    expect(save).toHaveClass("border-cream", "bg-cream", "text-ink");
    await user.click(discard);
    await user.click(save);
    expect(onDiscard).toHaveBeenCalledOnce();
    expect(onSave).toHaveBeenCalledOnce();
  });

  it("draws 'Saving': the tag, and both buttons off with Saving…", () => {
    renderSaveBar({ isDirty: true, isSaving: true });

    expect(screen.getByText("Unsaved changes")).toBeVisible();
    expect(screen.getByRole("button", { name: "Discard" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Saving…" })).toBeDisabled();
  });

  it("draws 'Save failed': the coral alert, Discard and Try again", async () => {
    const user = userEvent.setup();
    const { onSave } = renderSaveBar({ isDirty: true, failedMessage });

    expect(screen.getByRole("alert")).toHaveTextContent(failedMessage);
    expect(screen.getByRole("alert")).toHaveClass("text-[13px]", "text-danger");
    expect(screen.queryByText("Unsaved changes")).toBeNull();
    expect(screen.getByRole("button", { name: "Discard" })).toBeEnabled();
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(onSave).toHaveBeenCalledOnce();
  });

  it("keeps Save off while the changes can't be saved", () => {
    renderSaveBar({ isDirty: true, canSave: false });

    expect(screen.getByText("Unsaved changes")).toBeVisible();
    expect(screen.getByRole("button", { name: "Save Persona" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Discard" })).toBeEnabled();
  });

  it("sits on its own rounded panel", () => {
    renderSaveBar({ isDirty: false, placement: "alone" });

    expect(screen.getByRole("group", { name: "Save changes" })).toHaveClass(
      "rounded-tile",
      "border",
      "bg-panel",
      "px-5",
      "py-3",
    );
  });

  it("sits on the line at the foot of a box", () => {
    renderSaveBar({ isDirty: false, placement: "inside" });

    const bar = screen.getByRole("group", { name: "Save changes" });
    expect(bar).toHaveClass("border-t", "border-line", "px-5", "py-3");
    expect(bar).not.toHaveClass("bg-panel");
  });
});
