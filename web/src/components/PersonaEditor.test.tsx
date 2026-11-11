import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PersonaEditor } from "@/components/PersonaEditor";
import type { AdminSettings, ApiClient } from "@/lib/api-client";

const apiClient = {
  getAdminSettings: vi.fn<ApiClient["getAdminSettings"]>(),
  updateAdminSettings: vi.fn<ApiClient["updateAdminSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const settings: AdminSettings = {
  persona: {
    value: "You are Zeph.",
    updated_at: "2026-11-08T14:20:00Z",
    updated_by: "Maya Lin",
  },
};

describe("PersonaEditor", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getAdminSettings.mockResolvedValue(settings);
    apiClient.updateAdminSettings.mockImplementation(async (values) => ({
      persona: {
        value: String(values.persona),
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: "Maya Lin",
      },
    }));
  });

  it("shows the saved Persona, its length and who saved it", async () => {
    render(<PersonaEditor />);

    expect(await screen.findByLabelText("Persona text")).toHaveValue(
      "You are Zeph.",
    );
    expect(screen.getByText("13 characters")).toBeVisible();
    expect(screen.getByText(/Last saved .* by Maya Lin/)).toBeVisible();
    expect(screen.getByText(/The honesty rules must stay/)).toBeVisible();
  });

  it("saves an edited Persona", async () => {
    const user = userEvent.setup();
    render(<PersonaEditor />);
    const editor = await screen.findByLabelText("Persona text");

    await user.type(editor, " Be kind.");
    expect(screen.getByText("Unsaved changes")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Save Persona" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      persona: "You are Zeph. Be kind.",
    });
    expect(
      await screen.findByText("Saved. Zeph uses it from the next message."),
    ).toBeVisible();
    expect(screen.queryByText("Unsaved changes")).toBeNull();
  });

  it("discards unsaved edits", async () => {
    const user = userEvent.setup();
    render(<PersonaEditor />);
    const editor = await screen.findByLabelText("Persona text");

    await user.type(editor, " Oops.");
    await user.click(screen.getByRole("button", { name: "Discard" }));

    expect(editor).toHaveValue("You are Zeph.");
  });

  it("won't save an unchanged or empty Persona", async () => {
    const user = userEvent.setup();
    render(<PersonaEditor />);
    const editor = await screen.findByLabelText("Persona text");

    expect(screen.getByRole("button", { name: "Save Persona" })).toBeDisabled();
    await user.clear(editor);
    expect(screen.getByRole("button", { name: "Save Persona" })).toBeDisabled();
  });

  it("keeps the edit and says so when saving fails", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    render(<PersonaEditor />);
    const editor = await screen.findByLabelText("Persona text");

    await user.type(editor, " Be kind.");
    await user.click(screen.getByRole("button", { name: "Save Persona" }));

    expect(
      await screen.findByText(
        "Couldn’t save the Persona. Zeph keeps using the last saved version.",
      ),
    ).toBeVisible();
    expect(editor).toHaveValue("You are Zeph. Be kind.");
  });

  it("offers Try again when the Persona cannot be loaded", async () => {
    apiClient.getAdminSettings
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(settings);
    const user = userEvent.setup();
    render(<PersonaEditor />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByLabelText("Persona text")).toBeInTheDocument();
  });
});
