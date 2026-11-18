import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ConfirmDialog } from "@/components/ConfirmDialog";

/**
 * Renders an open Delete all memories dialog with spy handlers.
 *
 * @returns The confirm and cancel spies.
 */
function renderOpenDialog() {
  const onConfirm = vi.fn();
  const onCancel = vi.fn();
  render(
    <ConfirmDialog
      open
      title="Delete all memories?"
      body="Zeph will forget every memory it holds about you."
      cancelLabel="Keep them"
      confirmLabel="Delete all memories"
      onConfirm={onConfirm}
      onCancel={onCancel}
    />,
  );
  return { onConfirm, onCancel };
}

describe("ConfirmDialog", () => {
  it("names what will go and puts the safe choice first", () => {
    renderOpenDialog();

    const dialog = screen.getByRole("alertdialog", {
      name: "Delete all memories?",
    });
    const buttons = Array.from(dialog.querySelectorAll("button")).map(
      (button) => button.textContent,
    );
    expect(buttons).toEqual(["Keep them", "Delete all memories"]);
  });

  it("calls only onConfirm when confirm is pressed with the keyboard", async () => {
    const user = userEvent.setup();
    const { onConfirm, onCancel } = renderOpenDialog();

    screen.getByRole("button", { name: "Keep them" }).focus();
    await user.tab();
    expect(
      screen.getByRole("button", { name: "Delete all memories" }),
    ).toHaveFocus();
    await user.keyboard("{Enter}");

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("calls only onCancel when cancel is pressed with the keyboard", async () => {
    const user = userEvent.setup();
    const { onConfirm, onCancel } = renderOpenDialog();

    screen.getByRole("button", { name: "Keep them" }).focus();
    await user.keyboard(" ");

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("cancels when the browser closes it with Escape", () => {
    const { onConfirm, onCancel } = renderOpenDialog();

    fireEvent(
      screen.getByRole("alertdialog"),
      new Event("cancel", { cancelable: true }),
    );

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("shows nothing while closed", () => {
    render(
      <ConfirmDialog
        open={false}
        title="Delete all memories?"
        body="Zeph will forget every memory it holds about you."
        cancelLabel="Keep them"
        confirmLabel="Delete all memories"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });
});
