import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { EvalCaseForm } from "@/components/EvalCaseForm";
import { ApiError, type ApiClient, type FormShape } from "@/lib/api-client";
import {
  dayCaseDraft,
  evalDaySummaryFixtures,
} from "@/lib/design-fixtures/eval-day-summary";
import { personaShape, smallTalkCase } from "@/test/eval-cases";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  addEvalCase: vi.fn<ApiClient["addEvalCase"]>(),
  editEvalCase: vi.fn<ApiClient["editEvalCase"]>(),
};
const router = { push: vi.fn() };

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

describe("EvalCaseForm", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.editEvalCase.mockResolvedValue({
      ...smallTalkCase,
      edited: true,
    });
  });

  it("shows each section and what every field means", () => {
    renderWithQueries(
      <EvalCaseForm
        evalName="persona"
        shape={personaShape}
        existing={smallTalkCase}
      />,
    );

    const [messages] = screen.getAllByRole("region", { name: "Messages" });
    expect(
      within(messages).getByText("What the User sends, one after another."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("What the User writes, or the photo’s caption."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Whether this message is a crisis."),
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /Text/ })).toHaveValue(
      "hey there",
    );
    expect(screen.getByRole("switch", { name: "Photo Viewing" })).toBeChecked();
  });

  it("saves the edited case with what was typed and added", async () => {
    renderWithQueries(
      <EvalCaseForm
        evalName="persona"
        shape={personaShape}
        existing={smallTalkCase}
      />,
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Add a message" }),
    );
    const second = screen.getByRole("group", { name: "Message 2" });
    await userEvent.type(within(second).getByRole("textbox"), "and you?");
    await userEvent.click(
      screen.getByRole("switch", { name: "Photo Viewing" }),
    );
    await userEvent.selectOptions(
      screen.getByRole("combobox", { name: /Label/ }),
      "False alarm",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save case" }));

    expect(apiClient.editEvalCase).toHaveBeenCalledWith("small-talk", {
      messages: [{ text: "hey there" }, { text: "and you?" }],
      photo_viewing: false,
      kind: "false_alarm",
    });
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Saved. The next run uses it",
    );
  });

  it("shows the backend's message beside each field that is wrong", async () => {
    apiClient.addEvalCase.mockRejectedValue(
      new ApiError(422, "/api/admin/eval-cases", "The case has problems.", {
        key: "Another case has this key.",
        "messages.0.text": "Needs some text.",
        kind: "Pick one.",
      }),
    );
    renderWithQueries(<EvalCaseForm evalName="persona" shape={personaShape} />);

    await userEvent.type(screen.getByRole("textbox", { name: "Key" }), "plan");
    await userEvent.click(
      screen.getByRole("button", { name: "Add a message" }),
    );
    await userEvent.click(screen.getByRole("button", { name: "Add case" }));

    const alerts = await screen.findAllByRole("alert");
    expect(alerts.map((alert) => alert.textContent)).toEqual([
      "Another case has this key.",
      "Needs some text.",
      "Pick one.",
      "The case has problems.",
    ]);
    expect(apiClient.addEvalCase).toHaveBeenCalledWith("plan", "persona", {
      messages: [{ text: "" }],
      photo_viewing: true,
      kind: null,
    });
    expect(router.push).not.toHaveBeenCalled();
  });

  it("adds a new case and goes back to its Eval's list", async () => {
    apiClient.addEvalCase.mockResolvedValue({ ...smallTalkCase, key: "hi" });
    renderWithQueries(<EvalCaseForm evalName="persona" shape={personaShape} />);

    await userEvent.type(screen.getByRole("textbox", { name: "Key" }), "hi");
    await userEvent.click(screen.getByRole("button", { name: "Add case" }));

    expect(router.push).toHaveBeenCalledWith("/admin/evals/cases/persona");
  });

  it("shows an archived case without letting it change", () => {
    renderWithQueries(
      <EvalCaseForm
        evalName="persona"
        shape={personaShape}
        existing={{ ...smallTalkCase, archived: true }}
      />,
    );

    expect(screen.getByText(/This case is archived/)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: /Text/ })).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: "Save case" }),
    ).not.toBeInTheDocument();
  });

  it("draws a one-list section's entries straight in the panel, as the Day Summary form", async () => {
    const shapes = await evalDaySummaryFixtures.listEvalCaseShapes?.();
    const shape: FormShape = shapes?.day_summary ?? { sections: [] };
    apiClient.addEvalCase.mockResolvedValue({
      ...smallTalkCase,
      key: dayCaseDraft.key,
    });
    renderWithQueries(
      <EvalCaseForm
        evalName="day_summary"
        shape={shape}
        draft={dayCaseDraft}
      />,
    );

    const theDay = screen.getByRole("region", { name: "The day" });
    expect(
      within(theDay).queryByRole("heading", { name: "Messages" }),
    ).not.toBeInTheDocument();
    const first = within(theDay).getByRole("group", { name: "Message 1" });
    expect(within(first).getByRole("combobox", { name: "From" })).toHaveValue(
      "0",
    );
    expect(within(first).getByRole("textbox", { name: "Time" })).toHaveValue(
      "9:10 AM",
    );
    expect(
      within(first).getByRole("textbox", { name: "Text" }),
    ).not.toHaveAttribute("aria-describedby");
    expect(screen.getByRole("textbox", { name: "Key" })).toHaveValue(
      "guilt-and-job-worry",
    );

    await userEvent.click(
      screen.getByRole("button", { name: "Remove question 2" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Add a question" }),
    );
    const added = screen.getByRole("group", { name: "Question 2" });
    await userEvent.type(
      within(added).getByRole("textbox", { name: "Question" }),
      "Who did they snap at?",
    );
    await userEvent.type(
      within(added).getByRole("textbox", { name: "Expected answer" }),
      "Their sister.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Add case" }));

    expect(apiClient.addEvalCase).toHaveBeenCalledWith(
      "guilt-and-job-worry",
      "day_summary",
      {
        messages: dayCaseDraft.content.messages,
        questions: [
          {
            question: "What did the User feel guilty about?",
            expected: "Snapping at their sister in the morning.",
          },
          { question: "Who did they snap at?", expected: "Their sister." },
        ],
      },
    );
  });
});
