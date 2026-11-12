import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OnboardingFlow } from "@/components/OnboardingFlow";
import type { ApiClient, Me, PlatformContent } from "@/lib/api-client";

const apiClient = {
  getMe: vi.fn<ApiClient["getMe"]>(),
  getPlatformContent: vi.fn<ApiClient["getPlatformContent"]>(),
  completeOnboarding: vi.fn<ApiClient["completeOnboarding"]>(),
  getCheckIns: vi.fn<ApiClient["getCheckIns"]>(),
  getTelegramConnection: vi.fn<ApiClient["getTelegramConnection"]>(),
  createConnectionToken: vi.fn<ApiClient["createConnectionToken"]>(),
};
const router = { replace: vi.fn() };

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

const content: PlatformContent = {
  ai_notice: "Seeded notice: I am an AI, not a therapist.",
  ai_notice_short: "Zeph is an AI.",
  user_memory_explanation:
    "Seeded memory paragraph one.\n\nSeeded memory paragraph two.",
  onboarding_reason_choices: ["Being more present", "Relationships"],
};

function newUser(overrides: Partial<Me> = {}): Me {
  return {
    id: "user-1",
    email: "maya@example.com",
    name: null,
    onboarding_reasons: [],
    onboarding_note: null,
    country: null,
    time_zone: null,
    ai_notice_acknowledged_at: null,
    user_memory_enabled: true,
    onboarding_completed_at: null,
    role: "user",
    ...overrides,
  };
}

function setBrowserLanguages(languages: string[]) {
  Object.defineProperty(navigator, "languages", {
    value: languages,
    configurable: true,
  });
}

async function renderAtHelloStep() {
  render(<OnboardingFlow />);
  await screen.findByRole("heading", { name: "Hello. I’m Zeph." });
}

describe("OnboardingFlow", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getMe.mockResolvedValue(newUser());
    apiClient.getPlatformContent.mockResolvedValue(content);
    apiClient.getCheckIns.mockResolvedValue({
      enabled: false,
      frequency: "few_times_a_week",
      quiet_hours_start: "22:00:00",
      quiet_hours_end: "07:30:00",
      paused: false,
      paused_until: null,
      recent: [],
      kinds: [],
    });
    apiClient.completeOnboarding.mockImplementation(async () =>
      newUser({ onboarding_completed_at: "2026-11-11T09:00:00Z" }),
    );
    apiClient.getTelegramConnection.mockResolvedValue({
      connection: null,
      latest_token: {
        token: "7Q2K-ZEPH",
        deep_link_url: "https://t.me/zeph_bot?start=7Q2K-ZEPH",
        bot_username: "zeph_bot",
        expires_at: "2099-11-11T09:15:00Z",
        status: "active",
      },
    });
    setBrowserLanguages(["en-SG", "en"]);
  });

  it("shows the AI notice from platform settings", async () => {
    await renderAtHelloStep();

    expect(screen.getByText(content.ai_notice)).toBeInTheDocument();
  });

  it("cannot continue until the User gives a name and ticks I understand", async () => {
    const user = userEvent.setup();
    await renderAtHelloStep();
    const continueButton = screen.getByRole("button", { name: "Continue" });

    expect(continueButton).toBeDisabled();

    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    expect(continueButton).toBeDisabled();
    expect(
      screen.getByText("Tick the box above to continue."),
    ).toBeInTheDocument();

    await user.click(
      screen.getByRole("checkbox", {
        name: "I understand Zeph is an AI and not professional care",
      }),
    );
    expect(continueButton).toBeEnabled();
  });

  it("walks through the steps in order and saves every answer", async () => {
    const user = userEvent.setup();
    await renderAtHelloStep();

    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(
      screen.getByRole("heading", { name: "What brings you here?" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Relationships" }));
    expect(
      screen.getByRole("button", { name: "Relationships" }),
    ).toHaveAttribute("aria-pressed", "true");
    await user.type(
      screen.getByLabelText(/In your own words/),
      "New job, autopilot.",
    );
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(
      screen.getByRole("heading", { name: "Where are you?" }),
    ).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Time zone"), [
      "Asia/Singapore",
    ]);
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(
      screen.getByRole("heading", { name: "Should I check in?" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(
      screen.getByRole("heading", { name: "Can I remember things?" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(
      await screen.findByRole("heading", { name: "Let’s meet on Telegram." }),
    ).toBeInTheDocument();
    expect(apiClient.completeOnboarding).toHaveBeenCalledWith({
      name: "Maya",
      ai_notice_acknowledged: true,
      onboarding_reasons: ["Relationships"],
      onboarding_note: "New job, autopilot.",
      user_memory_enabled: true,
      country: "SG",
      time_zone: "Asia/Singapore",
      check_ins_enabled: false,
      check_in_frequency: "few_times_a_week",
      quiet_hours_start: "22:00",
      quiet_hours_end: "07:30",
    });
    expect(
      await screen.findByRole("link", { name: "Open in Telegram" }),
    ).toBeInTheDocument();
  });

  it("pre-fills the country from the browser without saying why it is asked", async () => {
    const user = userEvent.setup();
    await renderAtHelloStep();
    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Continue" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(screen.getByLabelText(/Country/)).toHaveValue("SG");
    expect(screen.getByText("Filled in from your browser")).toBeInTheDocument();
    expect(screen.queryByText(/Helpline/i)).not.toBeInTheDocument();
  });

  it("needs a country before leaving the location step", async () => {
    setBrowserLanguages(["en"]);
    const user = userEvent.setup();
    await renderAtHelloStep();
    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Continue" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(screen.getByLabelText(/Country/)).toHaveValue("");
    expect(screen.getByRole("button", { name: "Continue" })).toBeDisabled();

    await user.selectOptions(screen.getByLabelText(/Country/), ["MY"]);
    expect(screen.getByRole("button", { name: "Continue" })).toBeEnabled();
  });

  it("explains User Memory from platform settings, on by default and can be turned off", async () => {
    const user = userEvent.setup();
    await renderAtHelloStep();
    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    await user.click(screen.getByRole("checkbox"));
    for (let step = 0; step < 4; step++) {
      await user.click(screen.getByRole("button", { name: "Continue" }));
    }

    expect(
      screen.getByText("Seeded memory paragraph one."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Seeded memory paragraph two."),
    ).toBeInTheDocument();
    const memorySwitch = screen.getByRole("switch", {
      name: "Remember meaningful details",
    });
    expect(memorySwitch).toHaveAttribute("aria-checked", "true");

    await user.click(memorySwitch);
    await user.click(screen.getByRole("button", { name: "Continue" }));

    await screen.findByRole("heading", { name: "Let’s meet on Telegram." });
    expect(apiClient.completeOnboarding).toHaveBeenCalledWith(
      expect.objectContaining({ user_memory_enabled: false }),
    );
  });

  it("stays on the Memory step with a message when saving fails", async () => {
    apiClient.completeOnboarding.mockRejectedValue(new Error("down"));
    const user = userEvent.setup();
    await renderAtHelloStep();
    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    await user.click(screen.getByRole("checkbox"));
    for (let step = 0; step < 5; step++) {
      await user.click(screen.getByRole("button", { name: "Continue" }));
    }

    expect(
      await screen.findByText(
        "We couldn’t save your answers. Please try again.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Can I remember things?" }),
    ).toBeInTheDocument();
  });

  it("offers no conversation style, philosophy or tradition controls", async () => {
    const user = userEvent.setup();
    await renderAtHelloStep();
    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    await user.click(screen.getByRole("checkbox"));

    const seenText: string[] = [document.body.textContent ?? ""];
    for (let step = 0; step < 5; step++) {
      await user.click(screen.getByRole("button", { name: "Continue" }));
      seenText.push(document.body.textContent ?? "");
    }

    expect(seenText.join(" ")).not.toMatch(
      /style|tradition|how much philosophy/i,
    );
  });

  it("has Check-ins off by default, with frequency and quiet hours once turned on", async () => {
    const user = userEvent.setup();
    await renderAtHelloStep();
    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    await user.click(screen.getByRole("checkbox"));
    for (let step = 0; step < 3; step++) {
      await user.click(screen.getByRole("button", { name: "Continue" }));
    }

    const checkInsSwitch = screen.getByRole("switch", { name: "Check-ins" });
    expect(checkInsSwitch).toHaveAttribute("aria-checked", "false");
    expect(
      screen.queryByRole("group", { name: "How often" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("group", { name: "Quiet hours" }),
    ).not.toBeInTheDocument();

    await user.click(checkInsSwitch);
    await user.click(screen.getByRole("button", { name: "Most days" }));
    expect(screen.getByRole("button", { name: "Most days" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    const from = screen.getByLabelText("From");
    expect(from).toHaveValue("22:00");
    expect(screen.getByLabelText("Until")).toHaveValue("07:30");
    fireEvent.change(from, { target: { value: "21:00" } });
    expect(
      screen.getByText(/Never in your quiet hours, in your time zone/),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Continue" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    await screen.findByRole("heading", { name: "Let’s meet on Telegram." });
    expect(apiClient.completeOnboarding).toHaveBeenCalledWith(
      expect.objectContaining({
        check_ins_enabled: true,
        check_in_frequency: "most_days",
        quiet_hours_start: "21:00",
        quiet_hours_end: "07:30",
      }),
    );
  });

  it("sends a User who already finished onboarding to the Dashboard", async () => {
    apiClient.getMe.mockResolvedValue(
      newUser({ onboarding_completed_at: "2026-11-11T09:00:00Z" }),
    );

    render(<OnboardingFlow />);

    await vi.waitFor(() => expect(router.replace).toHaveBeenCalledWith("/"));
  });
});
