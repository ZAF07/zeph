import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { PromptsAndModels } from "@/components/PromptsAndModels";
import {
  ApiError,
  type AdminSettings,
  type ApiClient,
  type CoreServices,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

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
      extra_prompt_groups: [],
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
    renderWithQueries(<PromptsAndModels />);

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
    renderWithQueries(<PromptsAndModels />);
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
    renderWithQueries(<PromptsAndModels />);
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
              hint: null,
            },
          ],
          extra_prompt_groups: [],
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
    renderWithQueries(<PromptsAndModels />);
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

  it("says why when the backend refuses a save", async () => {
    apiClient.updateAdminSettings.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/settings",
        "The Features unavailable note must include {dashboard_url}, the link to the Dashboard.",
      ),
    );
    const user = userEvent.setup();
    renderWithQueries(<PromptsAndModels />);
    const card = within(
      await screen.findByRole("region", { name: "Response composition" }),
    );

    await user.type(card.getByLabelText("Prompt"), " Be warm.");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(
      await card.findByText(
        "The Features unavailable note must include {dashboard_url}, the link to the Dashboard.",
      ),
    ).toBeVisible();
  });

  describe("with extra prompts in groups", () => {
    beforeEach(() => {
      apiClient.getCoreServices.mockResolvedValue({
        services: [
          {
            ...coreServices.services[0],
            extra_prompt_groups: [
              {
                name: "Web search",
                prompts: [
                  {
                    key: "web_search_tool_description",
                    label: "web_search tool description",
                    hint: null,
                  },
                  {
                    key: "reply_web_search_instructions",
                    label: "Web search instructions",
                    hint: "Added when web search is offered.",
                  },
                ],
              },
              {
                name: "Memory and Knowledge",
                prompts: [
                  {
                    key: "reply_memory_intro",
                    label: "Memory intro",
                    hint: "Put before the User Memory.",
                  },
                ],
              },
            ],
          },
        ],
        model_choices: ["deepseek-chat"],
      });
      apiClient.getAdminSettings.mockResolvedValue({
        ...settings,
        web_search_tool_description: {
          value: "Search the web.",
          updated_at: "2026-11-01T00:00:00Z",
          updated_by: null,
        },
        reply_web_search_instructions: {
          value: "Say where it came from.",
          updated_at: "2026-11-01T00:00:00Z",
          updated_by: null,
        },
        reply_memory_intro: {
          value: "What you remember:",
          updated_at: "2026-11-01T00:00:00Z",
          updated_by: null,
        },
      });
      apiClient.updateAdminSettings.mockResolvedValue({});
    });

    it("folds each group shut until it is clicked", async () => {
      const user = userEvent.setup();
      renderWithQueries(<PromptsAndModels />);
      const card = within(
        await screen.findByRole("region", { name: "Response composition" }),
      );
      const instructions = card.getByLabelText("Web search instructions");
      expect(instructions).not.toBeVisible();
      expect(card.getByLabelText("Memory intro")).not.toBeVisible();

      await user.click(card.getByText("Web search"));

      expect(instructions).toBeVisible();
      expect(instructions).toHaveValue("Say where it came from.");
      expect(card.getByLabelText("web_search tool description")).toBeVisible();
      expect(card.getByLabelText("Memory intro")).not.toBeVisible();
    });

    it("shows a hint under the labels that have one", async () => {
      const user = userEvent.setup();
      renderWithQueries(<PromptsAndModels />);
      const card = within(
        await screen.findByRole("region", { name: "Response composition" }),
      );

      await user.click(card.getByText("Web search"));

      expect(
        card.getByLabelText("Web search instructions"),
      ).toHaveAccessibleDescription("Added when web search is offered.");
      expect(
        card.getByLabelText("web_search tool description"),
      ).not.toHaveAccessibleDescription();
    });

    it("saves the grouped notes with the prompt and model", async () => {
      const user = userEvent.setup();
      renderWithQueries(<PromptsAndModels />);
      const card = within(
        await screen.findByRole("region", { name: "Response composition" }),
      );

      await user.click(card.getByText("Memory and Knowledge"));
      await user.type(card.getByLabelText("Memory intro"), " Edited");
      await user.click(card.getByRole("button", { name: "Save" }));

      expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
        response_prompt: "Reply briefly.",
        response_model: "deepseek-chat",
        web_search_tool_description: "Search the web.",
        reply_web_search_instructions: "Say where it came from.",
        reply_memory_intro: "What you remember: Edited",
      });
    });
  });

  it("shows an empty state when no services are registered", async () => {
    apiClient.getCoreServices.mockResolvedValue({
      services: [],
      model_choices: [],
    });

    renderWithQueries(<PromptsAndModels />);

    expect(await screen.findByText("No services configured")).toBeVisible();
  });

  it("offers Try again when prompts cannot be loaded", async () => {
    apiClient.getCoreServices
      .mockRejectedValueOnce(new Error("down"))
      .mockResolvedValue(coreServices);
    const user = userEvent.setup();
    renderWithQueries(<PromptsAndModels />);

    await user.click(await screen.findByRole("button", { name: "Try again" }));

    expect(
      await screen.findByRole("region", { name: "Response composition" }),
    ).toBeVisible();
  });
});
