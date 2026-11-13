import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PromptsAndModels } from "@/components/PromptsAndModels";
import type { AdminSettings, ApiClient, CoreServices } from "@/lib/api-client";

const apiClient = {
  getAdminSettings: vi.fn<ApiClient["getAdminSettings"]>(),
  updateAdminSettings: vi.fn<ApiClient["updateAdminSettings"]>(),
  getCoreServices: vi.fn<ApiClient["getCoreServices"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const coreServices: CoreServices = {
  services: [
    {
      name: "Response composition",
      runs_when: "Every reply",
      description: "Writes Zeph’s reply.",
      prompt_key: "response_prompt",
      model_key: "response_model",
      extra_prompts: [],
    },
  ],
  model_choices: ["deepseek-chat", "deepseek-reasoner"],
};

const settings: AdminSettings = {
  response_prompt: {
    value: "Reply briefly.",
    updated_at: "2026-11-01T00:00:00Z",
    updated_by: null,
  },
  response_model: {
    value: "deepseek-chat",
    updated_at: "2026-11-01T00:00:00Z",
    updated_by: null,
  },
};

describe("PromptsAndModels", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getCoreServices.mockResolvedValue(coreServices);
    apiClient.getAdminSettings.mockResolvedValue(settings);
    apiClient.updateAdminSettings.mockImplementation(async (values) => ({
      response_prompt: {
        value: String(values.response_prompt),
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: "Maya Lin",
      },
      response_model: {
        value: String(values.response_model),
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: "Maya Lin",
      },
    }));
  });

  it("shows a card per core service with its model and prompt", async () => {
    render(<PromptsAndModels />);

    const card = within(
      await screen.findByRole("region", { name: "Response composition" }),
    );
    expect(card.getByText("Every reply")).toBeVisible();
    expect(card.getByText("Writes Zeph’s reply.")).toBeVisible();
    expect(card.getByLabelText("Model")).toHaveValue("deepseek-chat");
    expect(
      within(card.getByLabelText("Model"))
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["deepseek-chat", "deepseek-reasoner"]);
    expect(card.getByLabelText("Prompt")).toHaveValue("Reply briefly.");
    expect(card.getByText("Using the starting values")).toBeVisible();
  });

  it("saves a service's changed model and prompt together", async () => {
    const user = userEvent.setup();
    render(<PromptsAndModels />);
    const card = within(
      await screen.findByRole("region", { name: "Response composition" }),
    );
    expect(card.getByRole("button", { name: "Save" })).toBeDisabled();

    await user.selectOptions(card.getByLabelText("Model"), "deepseek-reasoner");
    await user.type(card.getByLabelText("Prompt"), " Be warm.");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      response_prompt: "Reply briefly. Be warm.",
      response_model: "deepseek-reasoner",
    });
    expect(await card.findByText(/Last saved .* by Maya Lin/)).toBeVisible();
    expect(card.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("says so when saving a service fails", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    render(<PromptsAndModels />);
    const card = within(
      await screen.findByRole("region", { name: "Response composition" }),
    );

    await user.type(card.getByLabelText("Prompt"), " Be warm.");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(
      await card.findByText(
        "Couldn’t save. The last saved prompt and model stay in use.",
      ),
    ).toBeVisible();
  });

  it("shows a service's extra prompts and saves them with its prompt and model", async () => {
    apiClient.getCoreServices.mockResolvedValue({
      services: [
        {
          name: "Photo viewing",
          runs_when: "Every photo, before the Safeguard",
          description: "Looks at each photo.",
          prompt_key: "photo_description_prompt",
          model_key: "photo_model",
          extra_prompts: [
            {
              key: "ask_about_photo_tool_description",
              label: "ask_about_photo tool description",
            },
          ],
        },
      ],
      model_choices: ["deepseek-chat"],
    });
    apiClient.getAdminSettings.mockResolvedValue({
      photo_description_prompt: {
        value: "Describe the photo.",
        updated_at: "2026-11-01T00:00:00Z",
        updated_by: null,
      },
      photo_model: {
        value: "deepseek-chat",
        updated_at: "2026-11-01T00:00:00Z",
        updated_by: null,
      },
      ask_about_photo_tool_description: {
        value: "Look again only when needed.",
        updated_at: "2026-11-01T00:00:00Z",
        updated_by: null,
      },
    });
    apiClient.updateAdminSettings.mockResolvedValue({});
    const user = userEvent.setup();
    render(<PromptsAndModels />);
    const card = within(
      await screen.findByRole("region", { name: "Photo viewing" }),
    );
    const toolDescription = card.getByLabelText(
      "ask_about_photo tool description",
    );
    expect(toolDescription).toHaveValue("Look again only when needed.");

    await user.type(toolDescription, " Ask one question.");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      photo_description_prompt: "Describe the photo.",
      photo_model: "deepseek-chat",
      ask_about_photo_tool_description:
        "Look again only when needed. Ask one question.",
    });
  });

  it("shows an empty state when no services are registered", async () => {
    apiClient.getCoreServices.mockResolvedValue({
      services: [],
      model_choices: [],
    });

    render(<PromptsAndModels />);

    expect(await screen.findByText("No services configured")).toBeVisible();
  });

  it("offers Try again when prompts cannot be loaded", async () => {
    apiClient.getCoreServices
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(coreServices);
    const user = userEvent.setup();
    render(<PromptsAndModels />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(
      await screen.findByRole("region", { name: "Response composition" }),
    ).toBeVisible();
  });
});
