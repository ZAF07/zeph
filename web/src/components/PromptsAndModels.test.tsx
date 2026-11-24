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
      thinking_key: "response_thinking",
      extra_prompts: [],
      extra_prompt_groups: [],
      limits: [],
    },
  ],
  model_choices: ["deepseek-flash", "deepseek-v4-pro"],
};

const settings: AdminSettings = {
  response_prompt: {
    hint: "",
    value: "Reply briefly.",
    updated_at: "2026-11-01T00:00:00Z",
    updated_by: null,
  },
  response_model: {
    hint: "",
    value: "deepseek-flash",
    updated_at: "2026-11-01T00:00:00Z",
    updated_by: null,
  },
  response_thinking: {
    hint: "",
    value: false,
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
        hint: "",
        value: String(values.response_prompt),
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: "Maya Lin",
      },
      response_model: {
        hint: "",
        value: String(values.response_model),
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: "Maya Lin",
      },
      response_thinking: {
        hint: "",
        value: values.response_thinking === true,
        updated_at: "2026-11-11T09:00:00Z",
        updated_by: "Maya Lin",
      },
    }));
  });

  it("shows a hint under the model and thinking switch, and above the prompt", async () => {
    apiClient.getAdminSettings.mockResolvedValue({
      response_prompt: {
        ...settings.response_prompt!,
        hint: "The Reply’s own instructions.",
      },
      response_model: {
        ...settings.response_model!,
        hint: "The model the Reply uses.",
      },
      response_thinking: {
        ...settings.response_thinking!,
        hint: "Whether the Reply thinks first.",
      },
    });
    renderWithQueries(<PromptsAndModels />);

    const card = within(
      await screen.findByRole("region", { name: "Response composition" }),
    );
    expect(card.getByLabelText("Prompt")).toHaveAccessibleDescription(
      "The Reply’s own instructions.",
    );
    expect(card.getByText("The model the Reply uses.")).toBeVisible();
    expect(card.getByText("Whether the Reply thinks first.")).toBeVisible();
  });

  it("shows a card per core service with its model, thinking and prompt", async () => {
    renderWithQueries(<PromptsAndModels />);

    const card = within(
      await screen.findByRole("region", { name: "Response composition" }),
    );
    expect(card.getByText("Every reply")).toBeVisible();
    expect(card.getByText("Writes Zeph’s reply.")).toBeVisible();
    expect(card.getByLabelText("Model")).toHaveValue("deepseek-flash");
    expect(
      within(card.getByLabelText("Model"))
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["deepseek-flash", "deepseek-v4-pro"]);
    expect(
      card.getByRole("switch", { name: "Thinking for Response composition" }),
    ).not.toBeChecked();
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

    await user.selectOptions(card.getByLabelText("Model"), "deepseek-v4-pro");
    await user.type(card.getByLabelText("Prompt"), " Be warm.");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      response_prompt: "Reply briefly. Be warm.",
      response_model: "deepseek-v4-pro",
      response_thinking: false,
    });
    expect(await card.findByText(/Last saved .* by Maya Lin/)).toBeVisible();
    expect(card.getByRole("button", { name: "Save" })).toBeDisabled();
  });

  it("shows each limit with its hint and saves a changed one with the service", async () => {
    const user = userEvent.setup();
    apiClient.getCoreServices.mockResolvedValue({
      ...coreServices,
      services: [
        {
          ...coreServices.services[0]!,
          limits: [
            {
              key: "pattern_keeping_days",
              label: "Days of evidence to include",
              hint: "How many days behind the evidence Pattern keeping reads.",
            },
          ],
        },
      ],
    });
    apiClient.getAdminSettings.mockResolvedValue({
      ...settings,
      pattern_keeping_days: {
        hint: "How many days behind the evidence Pattern keeping reads.",
        value: 14,
        updated_at: "2026-11-01T00:00:00Z",
        updated_by: null,
      },
    });
    renderWithQueries(<PromptsAndModels />);
    const card = within(
      await screen.findByRole("region", { name: "Response composition" }),
    );

    const days = card.getByLabelText("Days of evidence to include");
    expect(days).toHaveValue(14);
    expect(
      card.getByText(
        "How many days behind the evidence Pattern keeping reads.",
      ),
    ).toBeVisible();
    await user.clear(days);
    await user.type(days, "20");
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      response_prompt: "Reply briefly.",
      response_model: "deepseek-flash",
      response_thinking: false,
      pattern_keeping_days: 20,
    });
  });

  it("saves thinking switched on for a service", async () => {
    const user = userEvent.setup();
    renderWithQueries(<PromptsAndModels />);
    const card = within(
      await screen.findByRole("region", { name: "Response composition" }),
    );

    await user.click(
      card.getByRole("switch", { name: "Thinking for Response composition" }),
    );
    expect(
      card.getByRole("switch", { name: "Thinking for Response composition" }),
    ).toBeChecked();
    await user.click(card.getByRole("button", { name: "Save" }));

    expect(apiClient.updateAdminSettings).toHaveBeenCalledWith({
      response_prompt: "Reply briefly.",
      response_model: "deepseek-flash",
      response_thinking: true,
    });
    expect(await card.findByText(/Last saved .* by Maya Lin/)).toBeVisible();
    expect(
      card.getByRole("switch", { name: "Thinking for Response composition" }),
    ).toBeChecked();
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

    expect(await card.findByRole("alert")).toHaveTextContent(
      "Couldn’t save. The last saved prompt, model and thinking stay in use.",
    );
    expect(card.getByRole("button", { name: "Try again" })).toBeEnabled();
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
          thinking_key: "photo_thinking",
          extra_prompts: [
            {
              key: "ask_about_photo_tool_description",
              label: "ask_about_photo tool description",
              hint: "",
            },
          ],
          extra_prompt_groups: [],
          limits: [],
        },
      ],
      model_choices: ["deepseek-flash"],
    });
    apiClient.getAdminSettings.mockResolvedValue({
      photo_description_prompt: {
        hint: "",
        value: "Describe the photo.",
        updated_at: "2026-11-01T00:00:00Z",
        updated_by: null,
      },
      photo_model: {
        hint: "",
        value: "deepseek-flash",
        updated_at: "2026-11-01T00:00:00Z",
        updated_by: null,
      },
      ask_about_photo_tool_description: {
        hint: "",
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
      photo_model: "deepseek-flash",
      photo_thinking: false,
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
                    hint: "",
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
        model_choices: ["deepseek-flash"],
      });
      apiClient.getAdminSettings.mockResolvedValue({
        ...settings,
        web_search_tool_description: {
          hint: "",
          value: "Search the web.",
          updated_at: "2026-11-01T00:00:00Z",
          updated_by: null,
        },
        reply_web_search_instructions: {
          hint: "",
          value: "Say where it came from.",
          updated_at: "2026-11-01T00:00:00Z",
          updated_by: null,
        },
        reply_memory_intro: {
          hint: "",
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
        response_model: "deepseek-flash",
        response_thinking: false,
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

  describe("with several services", () => {
    beforeEach(() => {
      apiClient.getCoreServices.mockResolvedValue({
        services: [
          coreServices.services[0]!,
          {
            ...coreServices.services[0]!,
            name: "Safeguard",
            runs_when: "Every message",
            description: "Checks each message for risk.",
            prompt_key: "safeguard_prompt",
            model_key: "safeguard_model",
            thinking_key: "safeguard_thinking",
          },
        ],
        model_choices: coreServices.model_choices,
      });
    });

    it("starts with the first service open and the others folded", async () => {
      renderWithQueries(<PromptsAndModels />);

      expect(
        await screen.findByRole("button", { name: /Response composition/ }),
      ).toHaveAttribute("aria-expanded", "true");
      const safeguard = screen.getByRole("button", { name: /Safeguard/ });
      expect(safeguard).toHaveAttribute("aria-expanded", "false");
      expect(safeguard).toHaveTextContent("Checks each message for risk.");
      expect(safeguard).toHaveTextContent("Every message");
      const safeguardCard = within(
        screen.getByRole("region", { name: "Safeguard" }),
      );
      expect(safeguardCard.getByLabelText("Prompt")).not.toBeVisible();
    });

    it("opens a folded service when its row is clicked", async () => {
      const user = userEvent.setup();
      renderWithQueries(<PromptsAndModels />);

      await user.click(
        await screen.findByRole("button", { name: /Safeguard/ }),
      );

      const safeguardCard = within(
        screen.getByRole("region", { name: "Safeguard" }),
      );
      expect(safeguardCard.getByLabelText("Prompt")).toBeVisible();
      expect(
        screen.getByRole("button", { name: /Response composition/ }),
      ).toHaveAttribute("aria-expanded", "true");
    });

    it("opens and folds every service with Expand all and Collapse all", async () => {
      const user = userEvent.setup();
      renderWithQueries(<PromptsAndModels />);
      const responseRow = await screen.findByRole("button", {
        name: /Response composition/,
      });
      const safeguardRow = screen.getByRole("button", { name: /Safeguard/ });

      await user.click(screen.getByRole("button", { name: "Expand all" }));
      expect(responseRow).toHaveAttribute("aria-expanded", "true");
      expect(safeguardRow).toHaveAttribute("aria-expanded", "true");

      await user.click(screen.getByRole("button", { name: "Collapse all" }));
      expect(responseRow).toHaveAttribute("aria-expanded", "false");
      expect(safeguardRow).toHaveAttribute("aria-expanded", "false");
    });
  });

  it("puts a service's model and settings and its prompts in their own groups", async () => {
    renderWithQueries(<PromptsAndModels />);
    const card = within(
      await screen.findByRole("region", { name: "Response composition" }),
    );

    const settingsGroup = within(
      card.getByRole("group", { name: "Model & settings" }),
    );
    expect(settingsGroup.getByLabelText("Model")).toBeVisible();
    expect(
      settingsGroup.getByRole("switch", {
        name: "Thinking for Response composition",
      }),
    ).toBeVisible();
    const promptsGroup = within(card.getByRole("group", { name: "Prompts" }));
    expect(promptsGroup.getByLabelText("Prompt")).toHaveValue("Reply briefly.");
  });
});
