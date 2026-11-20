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
  steps: ["safeguard", "understanding", "reply_plan", "reply"],
  tokens_in: 1200,
  tokens_out: 80,
  duration_ms: 2400,
  error_count: 1,
  has_content: false,
  calls: [
    {
      id: "c1",
      step: "safeguard",
      model: "deepseek-flash",
      thinking: false,
      started_at: "2026-11-14T10:30:00Z",
      duration_ms: 400,
      tokens_in: 300,
      tokens_out: 2,
      error: null,
      tools_called: [],
      content: null,
      understanding_shape: null,
      check_in_shape: null,
      reply_plan_shape: null,
    },
    {
      id: "c4",
      step: "understanding",
      model: "deepseek-flash",
      thinking: true,
      started_at: "2026-11-14T10:30:00Z",
      duration_ms: 600,
      tokens_in: 800,
      tokens_out: 60,
      error: null,
      tools_called: [],
      content: null,
      understanding_shape: {
        intensity: "high",
        cause_known: false,
        struggling: true,
        past_look_ups: 2,
      },
      check_in_shape: null,
      reply_plan_shape: null,
    },
    {
      id: "c6",
      step: "reply_plan",
      model: "deepseek-flash",
      thinking: true,
      started_at: "2026-11-14T10:30:00Z",
      duration_ms: 900,
      tokens_in: 1600,
      tokens_out: 120,
      error: null,
      tools_called: [],
      content: null,
      understanding_shape: null,
      check_in_shape: null,
      reply_plan_shape: {
        need: "Be heard",
        lead_move: "Calm",
        support_move: null,
        next_move: null,
        threads_reminded: 3,
        threads_led_with: 1,
        threads_woven_in: 1,
        threads_left_alone: 1,
        threads_held_back: 1,
        read_formed: true,
        read_said: false,
        check_in_kinds_offered: 4,
        check_in_kind: "A follow-up",
      },
    },
    {
      id: "c5",
      step: "check_in",
      model: "deepseek-flash",
      thinking: true,
      started_at: "2026-11-14T10:30:01Z",
      duration_ms: 500,
      tokens_in: 700,
      tokens_out: 30,
      error: null,
      tools_called: [],
      content: null,
      understanding_shape: null,
      check_in_shape: { kind: "A follow-up", brought_up: true },
      reply_plan_shape: null,
    },
    {
      id: "c2",
      step: "reply",
      model: "deepseek-flash",
      thinking: false,
      started_at: "2026-11-14T10:30:01Z",
      duration_ms: 2000,
      tokens_in: 900,
      tokens_out: 78,
      error: "TimeoutError",
      tools_called: ["web_search"],
      content: null,
      understanding_shape: null,
      check_in_shape: null,
      reply_plan_shape: null,
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
      model: "deepseek-flash",
      thinking: true,
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
      check_in_shape: null,
      reply_plan_shape: null,
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
    expect(within(reply).getByText("deepseek-flash")).toBeInTheDocument();
    expect(within(reply).getByText("Thinking")).toBeInTheDocument();
    expect(within(reply).getByText("Off")).toBeInTheDocument();
    const understanding = screen.getByRole("article", {
      name: "Understanding",
    });
    expect(within(understanding).getByText("On")).toBeInTheDocument();
    expect(within(reply).getByText("900 in / 78 out")).toBeInTheDocument();
    expect(within(reply).getByText("2.0 s")).toBeInTheDocument();
    expect(within(reply).getByText("web_search")).toBeInTheDocument();
    expect(within(reply).getByText("TimeoutError")).toBeInTheDocument();
    expect(screen.getAllByText("No content kept for this User")).toHaveLength(
      5,
    );
    const safeguard = screen.getByRole("article", { name: "Safeguard" });
    expect(within(safeguard).getByText("None")).toBeInTheDocument();
    expect(screen.queryByText("Instructions")).not.toBeInTheDocument();
  });

  it("shows the Understanding and the Reply Plan as separate steps, each with its own facts", async () => {
    apiClient.getModelCallTrace.mockResolvedValue(plainUsersTrace);

    renderWithQueries(<ModelCallTraceView traceId="t1" />);

    const understanding = await screen.findByRole("article", {
      name: "Understanding",
    });
    const replyPlan = screen.getByRole("article", { name: "Reply Plan" });
    const factValue = (card: HTMLElement, label: string) =>
      within(card).getByText(label).nextElementSibling?.textContent;
    expect(factValue(understanding, "Mood intensity")).toBe("Strong");
    expect(factValue(understanding, "Cause known")).toBe("No");
    expect(factValue(understanding, "Struggling")).toBe("Yes");
    expect(factValue(understanding, "Past look-ups")).toBe("2");
    expect(
      within(understanding).queryByText("Need picked"),
    ).not.toBeInTheDocument();
    expect(factValue(replyPlan, "Need picked")).toBe("Be heard");
    expect(factValue(replyPlan, "Lead Move")).toBe("Calm");
    expect(factValue(replyPlan, "Supporting Move")).toBe("None");
    expect(factValue(replyPlan, "Life Threads reminded")).toBe("3");
    expect(factValue(replyPlan, "Threads brought up")).toBe(
      "2 (1 lead, 1 weave)",
    );
    expect(factValue(replyPlan, "Threads left alone")).toBe("1");
    expect(factValue(replyPlan, "Threads held back")).toBe("1");
    expect(factValue(replyPlan, "Read formed")).toBe("Yes");
    expect(factValue(replyPlan, "Read said")).toBe("No");
    expect(factValue(replyPlan, "Check-in Kinds offered")).toBe("4");
    expect(factValue(replyPlan, "Check-in Kind chosen")).toBe("A follow-up");
    expect(
      within(replyPlan).queryByText("Mood intensity"),
    ).not.toBeInTheDocument();
    const reply = screen.getByRole("article", { name: "Reply" });
    expect(within(reply).queryByText("Need picked")).not.toBeInTheDocument();
  });

  it("shows whether the reply brought up its Woven-in Check-in", async () => {
    apiClient.getModelCallTrace.mockResolvedValue(plainUsersTrace);

    renderWithQueries(<ModelCallTraceView traceId="t1" />);

    const checkIn = await screen.findByRole("article", { name: "Check-in" });
    const factValue = (label: string) =>
      within(checkIn).getByText(label).nextElementSibling?.textContent;
    expect(factValue("Check-in Kind")).toBe("A follow-up");
    expect(factValue("Brought up")).toBe("Yes");
    const reply = screen.getByRole("article", { name: "Reply" });
    expect(within(reply).queryByText("Brought up")).not.toBeInTheDocument();
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
