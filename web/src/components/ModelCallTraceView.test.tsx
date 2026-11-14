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
  steps: ["safeguard", "understanding", "reply"],
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
      understanding_shape: null,
    },
    {
      id: "c4",
      step: "understanding",
      model: "deepseek-chat",
      started_at: "2026-11-14T10:30:00Z",
      duration_ms: 600,
      tokens_in: 800,
      tokens_out: 60,
      error: null,
      tools_called: [],
      content: null,
      understanding_shape: {
        need: "Be heard",
        intensity: "high",
        cause_known: false,
        threads_reminded: 3,
        threads_led_with: 1,
        threads_woven_in: 1,
        threads_left_alone: 1,
        threads_held_back: 1,
        past_look_ups: 2,
      },
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
      understanding_shape: null,
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
      understanding_shape: null,
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
      3,
    );
    expect(screen.queryByText("Instructions")).not.toBeInTheDocument();
  });

  it("shows the shape of the Understanding's decision", async () => {
    apiClient.getModelCallTrace.mockResolvedValue(plainUsersTrace);

    renderWithQueries(<ModelCallTraceView traceId="t1" />);

    const understanding = await screen.findByRole("article", {
      name: "Understanding",
    });
    const factValue = (label: string) =>
      within(understanding).getByText(label).nextElementSibling?.textContent;
    expect(factValue("Need picked")).toBe("Be heard");
    expect(factValue("Mood intensity")).toBe("High");
    expect(factValue("Cause known")).toBe("No");
    expect(factValue("Life Threads reminded")).toBe("3");
    expect(factValue("Threads brought up")).toBe("2 (1 lead, 1 weave)");
    expect(factValue("Threads left alone")).toBe("1");
    expect(factValue("Threads held back")).toBe("1");
    expect(factValue("Past look-ups")).toBe("2");
    const reply = screen.getByRole("article", { name: "Reply" });
    expect(within(reply).queryByText("Need picked")).not.toBeInTheDocument();
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
