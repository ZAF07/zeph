import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { OnboardingFlow } from "@/components/OnboardingFlow";
import type { ApiClient, Me, PlatformContent } from "@/lib/api-client";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";
import { renderWithQueries } from "@/test/render-with-queries";

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
  onboarding_reason_choices: ["Being more present", "Relationships"],
  message_retention_days: 30,
};

const editedCopy = {
  ...seedCopy(),
  "onboarding.hello.ai_notice": "Edited notice: I am an AI, not a therapist.",
  "shared.memory_explanation":
    "Edited memory paragraph one.\n\nEdited memory paragraph two.",
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
    user_memory_available: true,
    photo_viewing_enabled: true,
    photo_viewing_available: true,
    directness: "balanced",
    personal_stickers_available: false,
    show_pattern_noticing_notice: false,
    onboarding_completed_at: null,
    role: "user",
    changed_in_chat: {},
    ...overrides,
  };
}

function setBrowserLanguages(languages: string[]) {
  Object.defineProperty(navigator, "languages", {
    value: languages,
    configurable: true,
  });
}

async function renderAtHelloStep(copy = seedCopy()) {
  renderWithQueries(<OnboardingFlow copy={copy} />);
  await screen.findByRole("heading", { name: "Hello. I’m Zeph." });
}

describe("OnboardingFlow", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getMe.mockResolvedValue(newUser());
    apiClient.getPlatformContent.mockResolvedValue(content);
    apiClient.getCheckIns.mockResolvedValue({
      enabled: false,
      available: true,
      frequency: "few_times_a_week",
      quiet_hours_start: "22:00:00",
      quiet_hours_end: "07:30:00",
      paused: false,
      paused_until: null,
      recent: [],
      kinds: [],
      changed_by_admin: {},
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

  it("shows the AI notice from Copy", async () => {
    await renderAtHelloStep(editedCopy);

    expect(
      screen.getByText("Edited notice: I am an AI, not a therapist."),
    ).toBeInTheDocument();
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

  it("explains User Memory from Shared Copy, on by default and can be turned off", async () => {
    const user = userEvent.setup();
    await renderAtHelloStep(editedCopy);
    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    await user.click(screen.getByRole("checkbox"));
    for (let step = 0; step < 4; step++) {
      await user.click(screen.getByRole("button", { name: "Continue" }));
    }

    expect(
      screen.getByText("Edited memory paragraph one."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Edited memory paragraph two."),
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
      screen.queryByText(/Never in your quiet hours/),
    ).not.toBeInTheDocument();

    await user.click(checkInsSwitch);
    await user.click(screen.getByRole("button", { name: "Most days" }));
    expect(screen.getByRole("button", { name: "Most days" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(
      screen.getByText(/Never in your quiet hours, in your time zone/),
    ).toHaveTextContent(
      "Never in your quiet hours, in your time zone: 10:00 PM to 7:30 AM",
    );
    await user.click(screen.getByRole("button", { name: "Continue" }));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    await screen.findByRole("heading", { name: "Let’s meet on Telegram." });
    expect(apiClient.completeOnboarding).toHaveBeenCalledWith(
      expect.objectContaining({
        check_ins_enabled: true,
        check_in_frequency: "most_days",
        quiet_hours_start: "22:00",
        quiet_hours_end: "07:30",
      }),
    );
  });

  it("shows one step at a time", async () => {
    await renderAtHelloStep();

    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByText("Step 1 of 6")).toBeInTheDocument();
  });

  it("stacks all six steps for the design sheet, each drawn ready to continue", async () => {
    renderWithQueries(<OnboardingFlow copy={seedCopy()} showAllSteps />);

    await screen.findByRole("heading", { name: "Hello. I’m Zeph." });
    expect(
      screen.getAllByRole("heading", { level: 1 }).map((h) => h.textContent),
    ).toEqual([
      "Hello. I’m Zeph.",
      "What brings you here?",
      "Where are you?",
      "Should I check in?",
      "Can I remember things?",
      "Let’s meet on Telegram.",
    ]);
    expect(screen.getByText("Step 6 of 6")).toBeInTheDocument();
    for (const button of screen.getAllByRole("button", { name: "Continue" })) {
      expect(button).toBeEnabled();
    }
    expect(
      screen.queryByText("Tell me what to call you to continue."),
    ).not.toBeInTheDocument();
    expect(screen.getByText("Filled in from your browser")).toBeInTheDocument();
  });

  it("shows only Copy text on every step, apart from the reason choices", async () => {
    apiClient.getPlatformContent.mockResolvedValue({
      ...content,
      onboarding_reason_choices: ["⟦platform reason⟧"],
    });
    apiClient.getCheckIns.mockResolvedValue({
      ...(await apiClient.getCheckIns()),
      enabled: true,
    });
    apiClient.getMe.mockResolvedValue(newUser({ name: "Maya" }));

    const { container } = renderWithQueries(
      <OnboardingFlow copy={markedCopy()} showAllSteps />,
    );
    await screen.findByRole("link", {
      name: /⟦connect_telegram.card.open_button⟧/,
    });

    const steps = container.querySelectorAll("section");
    expect(steps).toHaveLength(6);
    for (const step of steps) {
      const words = step.cloneNode(true) as HTMLElement;
      words
        .querySelectorAll("option:not([disabled])")
        .forEach((country) => country.remove());
      expect(wordsNotFromCopy(words)).toEqual([]);
    }
    expect(
      screen.getByRole("textbox", { name: "⟦onboarding.hello.name_label⟧" }),
    ).toHaveAttribute("placeholder", "⟦onboarding.hello.name_hint⟧");
    expect(
      screen.getByRole("textbox", {
        name: /⟦onboarding.intentions.note_label⟧/,
      }),
    ).toHaveAttribute("placeholder", "⟦onboarding.intentions.note_hint⟧");
  });

  it("shows an Admin's changed question, with the reason choices still from Platform Settings", async () => {
    const user = userEvent.setup();
    renderWithQueries(
      <OnboardingFlow
        copy={{
          ...seedCopy(),
          "onboarding.intentions.heading": "What made you come today?",
          "onboarding.progress.step_count": "{step}/{count}",
        }}
      />,
    );
    await screen.findByRole("heading", { name: "Hello. I’m Zeph." });
    expect(screen.getByText("1/6")).toBeInTheDocument();

    await user.type(screen.getByLabelText("What should I call you?"), "Maya");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: "Continue" }));

    expect(
      screen.getByRole("heading", { name: "What made you come today?" }),
    ).toBeInTheDocument();
    expect(screen.getByText("2/6")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Being more present" }),
    ).toBeInTheDocument();
  });

  it("sends a User who already finished onboarding to the Dashboard", async () => {
    apiClient.getMe.mockResolvedValue(
      newUser({ onboarding_completed_at: "2026-11-11T09:00:00Z" }),
    );

    renderWithQueries(<OnboardingFlow copy={seedCopy()} />);

    await vi.waitFor(() => expect(router.replace).toHaveBeenCalledWith("/"));
  });
});
