import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { JudgeSettingsForm } from "@/components/JudgeSettingsForm";
import { ApiError, type ApiClient, type JudgeSettings } from "@/lib/api-client";
import { shapeField } from "@/test/eval-cases";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  saveJudgeSettings: vi.fn<ApiClient["saveJudgeSettings"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const settings: JudgeSettings = {
  shape: {
    sections: [
      {
        title: "Model",
        description: "The model that marks cases.",
        fields: [
          shapeField({
            name: "model",
            label: "Model",
            kind: "choice",
            required: true,
            description: "The model the Judge asks.",
            options: [
              { value: "deepseek-flash", label: "deepseek-flash" },
              { value: "deepseek-v4-pro", label: "deepseek-v4-pro" },
            ],
          }),
          shapeField({
            name: "thinking",
            label: "Thinking",
            kind: "on_off",
            description: "Whether the Judge thinks before it answers.",
          }),
        ],
      },
      {
        title: "Prompts",
        description: "What the Judge is told.",
        fields: [
          shapeField({
            name: "persona_instructions",
            label: "Rules prompt",
            kind: "long_text",
            required: true,
            description: "How the Judge checks replies against rules.",
          }),
        ],
      },
    ],
  },
  values: {
    model: "deepseek-flash",
    thinking: false,
    persona_instructions: "Judge strictly.",
  },
};

describe("JudgeSettingsForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("explains each setting and saves the Judge", async () => {
    apiClient.saveJudgeSettings.mockResolvedValue(settings);
    renderWithQueries(<JudgeSettingsForm settings={settings} />);

    expect(screen.getByText("The model the Judge asks.")).toBeInTheDocument();
    expect(
      screen.getByText("How the Judge checks replies against rules."),
    ).toBeInTheDocument();
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: "Model" }),
      "deepseek-v4-pro",
    );
    await userEvent.click(screen.getByRole("switch", { name: "Thinking" }));
    await userEvent.click(screen.getByRole("button", { name: "Save Judge" }));

    expect(apiClient.saveJudgeSettings).toHaveBeenCalledWith({
      model: "deepseek-v4-pro",
      thinking: true,
      persona_instructions: "Judge strictly.",
    });
    expect(await screen.findByRole("status")).toHaveTextContent(
      "The next run uses it",
    );
  });

  it("shows why a save was refused beside the field", async () => {
    apiClient.saveJudgeSettings.mockRejectedValue(
      new ApiError(422, "/api/admin/eval-judge", "See each field.", {
        persona_instructions: "Needs some text.",
      }),
    );
    renderWithQueries(<JudgeSettingsForm settings={settings} />);

    await userEvent.clear(
      screen.getByRole("textbox", { name: /Rules prompt/ }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Save Judge" }));

    const alerts = await screen.findAllByRole("alert");
    expect(alerts.map((alert) => alert.textContent)).toEqual([
      "Needs some text.",
      "See each field.",
    ]);
  });
});
