import { screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ModelCallTraceView } from "@/components/ModelCallTraceView";
import {
  ApiError,
  type ApiClient,
  type ModelCallTraceDetails,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getModelCallTrace: vi.fn<ApiClient["getModelCallTrace"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

const plainUsersTrace: ModelCallTraceDetails = {
  trace_id: "t1",
  kind: "message",
  user_id: "u1",
  user_name: "Maya Lin",
  user_email: "maya@example.com",
  started_at: "2026-11-14T10:30:00Z",
  steps: ["safeguard", "reply"],
  tokens_in: 1200,
  tokens_out: 80,
  duration_ms: 2400,
  error_count: 1,
  has_content: false,
  calls: [
    {
      id: "c1",
      step: "safeguard",
      model: "deepseek-chat",
      started_at: "2026-11-14T10:30:00Z",
      duration_ms: 400,
      tokens_in: 300,
      tokens_out: 2,
      error: null,
      tools_called: [],
      content: null,
    },
    {
      id: "c2",
      step: "reply",
      model: "deepseek-chat",
      started_at: "2026-11-14T10:30:01Z",
      duration_ms: 2000,
      tokens_in: 900,
      tokens_out: 78,
      error: "TimeoutError",
      tools_called: ["web_search"],
      content: null,
    },
  ],
};

const adminsTrace: ModelCallTraceDetails = {
  ...plainUsersTrace,
  user_name: "Owner",
  error_count: 0,
  has_content: true,
  calls: [
    {
      id: "c3",
      step: "reply",
      model: "deepseek-reasoner",
      started_at: "2026-11-14T10:30:01Z",
      duration_ms: 2000,
      tokens_in: 900,
      tokens_out: 78,
      error: null,
      tools_called: ["web_search"],
      content: {
        instructions: "You are Zeph.",
        history: [{ role: "user", text: "tell me about lighthouses" }],
        tools_offered: [
          {
            name: "web_search",
            description: "Search the web.",
            parameters: {},
          },
        ],
        tool_calls: [
          {
            name: "web_search",
            arguments: { query: "lighthouses" },
            result: "Lighthouses guide ships.",
          },
        ],
        response: "They guide ships home.",
        reasoning: "They want facts.",
      },
    },
  ],
};

describe("ModelCallTraceView", () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it("shows each call's step, model, tokens, time, tools and error, with no content for a plain User", async () => {
    apiClient.getModelCallTrace.mockResolvedValue(plainUsersTrace);

    renderWithQueries(<ModelCallTraceView traceId="t1" />);

    const reply = await screen.findByRole("article", { name: "Reply" });
    expect(apiClient.getModelCallTrace).toHaveBeenCalledWith("t1");
    expect(within(reply).getByText("deepseek-chat")).toBeInTheDocument();
    expect(within(reply).getByText("900 in / 78 out")).toBeInTheDocument();
    expect(within(reply).getByText("2.0 s")).toBeInTheDocument();
    expect(within(reply).getByText("web_search")).toBeInTheDocument();
    expect(within(reply).getByText("TimeoutError")).toBeInTheDocument();
    expect(screen.getAllByText("No content kept for this User")).toHaveLength(
      2,
    );
    expect(screen.queryByText("Instructions")).not.toBeInTheDocument();
  });

  it("shows full content for an Admin's own chat, tool calls included", async () => {
    apiClient.getModelCallTrace.mockResolvedValue(adminsTrace);

    renderWithQueries(<ModelCallTraceView traceId="t1" />);

    const reply = await screen.findByRole("article", { name: "Reply" });
    expect(within(reply).getByText("You are Zeph.")).toBeInTheDocument();
    expect(
      within(reply).getByText("tell me about lighthouses"),
    ).toBeInTheDocument();
    expect(
      within(reply).getByText(/"query": "lighthouses"/),
    ).toBeInTheDocument();
    expect(
      within(reply).getByText("Lighthouses guide ships."),
    ).toBeInTheDocument();
    expect(
      within(reply).getByText("They guide ships home."),
    ).toBeInTheDocument();
    expect(within(reply).getByText("They want facts.")).toBeInTheDocument();
  });

  it("says when the trace no longer exists", async () => {
    apiClient.getModelCallTrace.mockRejectedValue(
      new ApiError(404, "/api/admin/model-calls/gone"),
    );

    renderWithQueries(<ModelCallTraceView traceId="gone" />);

    expect(await screen.findByText("This trace is gone")).toBeInTheDocument();
  });
});
