import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PersonaEditor } from "@/components/PersonaEditor";
import type { AdminSettings, ApiClient } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getAdminSettings: vi.fn<ApiClient["getAdminSettings"]>(),
  updateAdminSettings: vi.fn<ApiClient["updateAdminSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const settings: AdminSettings = {
  persona: {
    hint: "",
    value: "You are Zeph.",
    updated_at: "2026-11-08T14:20:00Z",
    updated_by: "Maya Lin",
  },
  persona_outlook: {
    hint: "How Zeph sees people and what helps them grow.",
    value: "People grow by being seen.",
    updated_at: "2026-11-08T14:20:00Z",
    updated_by: null,
  },
};

describe("PersonaEditor", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    window.history.replaceState(null, "", "/admin/persona");
    apiClient.getAdminSettings.mockResolvedValue(settings);
    apiClient.updateAdminSettings.mockImplementation(async (values) => {
      const saved = { ...settings };
      for (const [key, value] of Object.entries(values)) {
        saved[key] = {
          hint: settings[key]?.hint ?? "",
          value: String(value),
          updated_at: "2026-11-11T09:00:00Z",
          updated_by: "Maya Lin",
        };
      }
      return saved;
    });
  });

  it("shows the saved Persona, its length and who saved it", async () => {
    renderWithQueries(<PersonaEditor initialTab="voice" />);

    expect(await screen.findByLabelText("Voice text")).toHaveValue(
      "You are Zeph.",
    );
    expect(screen.getByText("13 characters")).toBeVisible();
    expect(screen.getByText(/Last saved .* by Maya Lin/)).toBeVisible();
    expect(
      screen.getByText("Changes apply to the next message after saving."),
    ).toBeVisible();
  });

  it("shows the voice's name and hint above its editor", async () => {
    apiClient.getAdminSettings.mockResolvedValue({
      ...settings,
      persona: {
        ...settings.persona!,
        hint: "Who Zeph is. Put in front of the Reply’s instructions.",
      },
    });
    renderWithQueries(<PersonaEditor initialTab="voice" />);

    const editor = await screen.findByLabelText("Voice text");
    expect(
      screen.getByText(
        "Who Zeph is. Put in front of the Reply’s instructions.",
      ),
    ).toBeVisible();
    expect(editor).toHaveAccessibleDescription(
      "Who Zeph is. Put in front of the Reply’s instructions.",
    );
  });

  it("shows the Outlook tab, its hint and starting text from ?tab=outlook", async () => {
    renderWithQueries(<PersonaEditor initialTab="outlook" />);

    const editor = await screen.findByLabelText("Outlook text");
    expect(editor).toHaveValue("People grow by being seen.");
    expect(editor).toHaveAccessibleDescription(
      "How Zeph sees people and what helps them grow.",
    );
    expect(screen.getByRole("tab", { name: "Outlook" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByText("Using the starting values")).toBeVisible();
    expect(
      screen.getByText("Changes apply to the next reply after saving."),
    ).toBeVisible();
  });

  it("keeps unsaved text in one tab while the other is shown", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PersonaEditor initialTab="voice" />);
    await user.type(await screen.findByLabelText("Voice text"), " Be kind.");

    await user.click(screen.getByRole("tab", { name: "Outlook" }));
    expect(window.location.search).toBe("?tab=outlook");
    await user.type(screen.getByLabelText("Outlook text"), " Gently.");
    await user.click(screen.getByRole("tab", { name: "Voice" }));

    expect(window.location.search).toBe("");
    expect(screen.getByLabelText("Voice text")).toHaveValue(
      "You are Zeph. Be kind.",
    );
    expect(screen.getByText("Unsaved changes")).toBeVisible();
    await user.click(screen.getByRole("tab", { name: "Outlook" }));
    expect(screen.getByLabelText("Outlook text")).toHaveValue(
      "People grow by being seen. Gently.",
    );
  });

  it("saves only the Outlook from the Outlook tab", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PersonaEditor initialTab="outlook" />);

    await user.type(await screen.findByLabelText("Outlook text"), " Gently.");
    await user.click(screen.getByRole("button", { name: "Save Outlook" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      persona_outlook: "People grow by being seen. Gently.",
    });
    expect(
      await screen.findByText("Saved. Zeph uses it from the next reply."),
    ).toBeVisible();
  });

  it("saves an edited Persona", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PersonaEditor initialTab="voice" />);
    const editor = await screen.findByLabelText("Voice text");

    await user.type(editor, " Be kind.");
    expect(screen.getByText("Unsaved changes")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Save voice" }));

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
    renderWithQueries(<PersonaEditor initialTab="voice" />);
    const editor = await screen.findByLabelText("Voice text");

    await user.type(editor, " Oops.");
    await user.click(screen.getByRole("button", { name: "Discard" }));

    expect(editor).toHaveValue("You are Zeph.");
  });

  it("won't save an unchanged or empty Persona", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PersonaEditor initialTab="voice" />);
    const editor = await screen.findByLabelText("Voice text");

    expect(screen.getByRole("button", { name: "Save voice" })).toBeDisabled();
    await user.clear(editor);
    expect(screen.getByRole("button", { name: "Save voice" })).toBeDisabled();
  });

  it("keeps the edit and says so when saving fails", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    renderWithQueries(<PersonaEditor initialTab="voice" />);
    const editor = await screen.findByLabelText("Voice text");

    await user.type(editor, " Be kind.");
    await user.click(screen.getByRole("button", { name: "Save voice" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Couldn’t save. Your text is still here.",
    );
    expect(editor).toHaveValue("You are Zeph. Be kind.");

    apiClient.updateAdminSettings.mockResolvedValue({
      ...settings,
      persona: {
        hint: "",
        value: "You are Zeph. Be kind.",
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: "Maya Lin",
      },
    });
    await user.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByText("Saved. Zeph uses it from the next message."),
    ).toBeVisible();
  });

  it("offers Try again when the Persona cannot be loaded", async () => {
    apiClient.getAdminSettings
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(settings);
    const user = userEvent.setup();
    renderWithQueries(<PersonaEditor initialTab="voice" />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(await screen.findByLabelText("Voice text")).toBeInTheDocument();
  });
});
