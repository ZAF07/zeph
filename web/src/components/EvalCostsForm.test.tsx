import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EvalCostsForm } from "@/components/EvalCostsForm";
import { ApiError, type ApiClient, type EvalCosts } from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getEvalCosts: vi.fn<ApiClient["getEvalCosts"]>(),
  saveEvalCosts: vi.fn<ApiClient["saveEvalCosts"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const seeded: EvalCosts = {
  prices: [
    { model: "deepseek-flash", sgd_in: 0.38, sgd_out: 1.54 },
    { model: "deepseek-v4-pro", sgd_in: null, sgd_out: null },
  ],
  token_limit: 1_000_000,
};

describe("EvalCostsForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getEvalCosts.mockResolvedValue(seeded);
    apiClient.saveEvalCosts.mockImplementation((costs) =>
      Promise.resolve(costs),
    );
  });

  it("marks a model with no price and saves prices with the limit", async () => {
    renderWithQueries(<EvalCostsForm />);

    expect(await screen.findByText("no price set")).toBeInTheDocument();
    const flashOut = screen.getByLabelText("deepseek-flash SGD out");
    await userEvent.clear(flashOut);
    await userEvent.type(flashOut, "2");
    await userEvent.type(
      screen.getByLabelText("deepseek-v4-pro SGD in"),
      "1.69",
    );
    await userEvent.type(
      screen.getByLabelText("deepseek-v4-pro SGD out"),
      "5.07",
    );
    const limit = screen.getByLabelText("Most tokens one run may use");
    await userEvent.clear(limit);
    await userEvent.type(limit, "500000");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(apiClient.saveEvalCosts).toHaveBeenCalledWith({
      prices: [
        { model: "deepseek-flash", sgd_in: 0.38, sgd_out: 2 },
        { model: "deepseek-v4-pro", sgd_in: 1.69, sgd_out: 5.07 },
      ],
      token_limit: 500_000,
    });
    expect(await screen.findByRole("status")).toHaveTextContent("Saved");
  });

  it("adds a model and shows the backend's reason when a save is refused", async () => {
    apiClient.saveEvalCosts.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/eval-costs",
        "Give x a price for tokens in and out, or neither.",
      ),
    );
    renderWithQueries(<EvalCostsForm />);

    await userEvent.click(
      await screen.findByRole("button", { name: "Add a model" }),
    );
    await userEvent.type(screen.getByLabelText("Model name"), "x");
    await userEvent.type(screen.getByLabelText("x SGD in"), "1");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(apiClient.saveEvalCosts.mock.calls[0]?.[0].prices[2]).toEqual({
      model: "x",
      sgd_in: 1,
      sgd_out: null,
    });
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Give x a price for tokens in and out, or neither.",
    );
  });
});
