import { act, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgeDocumentView } from "@/components/KnowledgeDocumentView";
import {
  ApiError,
  type ApiClient,
  type KnowledgeDocumentWithText,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  getKnowledgeDocument: vi.fn<ApiClient["getKnowledgeDocument"]>(),
  updateKnowledgeDocumentDetails:
    vi.fn<ApiClient["updateKnowledgeDocumentDetails"]>(),
  saveKnowledgeDocumentText: vi.fn<ApiClient["saveKnowledgeDocumentText"]>(),
  replaceKnowledgeDocumentFile:
    vi.fn<ApiClient["replaceKnowledgeDocumentFile"]>(),
  retryKnowledgeDocument: vi.fn<ApiClient["retryKnowledgeDocument"]>(),
  deleteKnowledgeDocument: vi.fn<ApiClient["deleteKnowledgeDocument"]>(),
};

const router = { push: vi.fn() };

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

const breathing: KnowledgeDocumentWithText = {
  id: "breathing",
  title: "Mindful breathing",
  source: "Owner’s summary",
  tradition: "Mindfulness",
  file_name: "mindful-breathing.md",
  file_type: "markdown",
  status: "ready",
  failure_reason: null,
  text_edited: false,
  created_at: "2026-10-02T09:00:00Z",
  text: "# Mindful breathing\n\nNotice the **breath** entering.",
};

const scan: KnowledgeDocumentWithText = {
  ...breathing,
  id: "scan",
  title: "Being and Time (excerpt)",
  file_name: "being.pdf",
  file_type: "pdf",
  status: "failed",
  failure_reason: "Scanned PDF — no text found",
  text: null,
};

describe("KnowledgeDocumentView", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.getKnowledgeDocument.mockResolvedValue(breathing);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows the document's details and its text in the editor", async () => {
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);

    expect(
      await screen.findByRole("heading", {
        name: "Mindful breathing",
        level: 1,
      }),
    ).toBeInTheDocument();
    expect(apiClient.getKnowledgeDocument).toHaveBeenCalledWith("breathing");
    const details = within(screen.getByRole("form", { name: "Details" }));
    expect(details.getByLabelText("Title")).toHaveValue("Mindful breathing");
    expect(details.getByLabelText("Source / author")).toHaveValue(
      "Owner’s summary",
    );
    expect(details.getByLabelText("Tradition")).toHaveValue("Mindfulness");
    expect(
      details.getByText("Markdown · mindful-breathing.md"),
    ).toBeInTheDocument();
    expect(details.getByText("2 Oct 2026")).toBeInTheDocument();
    expect(
      details.getByRole("button", { name: "Save details" }),
    ).toBeDisabled();
    expect(screen.getAllByText("Ready").length).toBeGreaterThan(0);
    expect(screen.queryByText("Edited")).toBeNull();
    const editor = screen.getByRole("textbox", {
      name: "Text of Mindful breathing",
    });
    expect(editor).toHaveAttribute("aria-readonly", "false");
    expect(editor).toHaveTextContent("Notice the **breath** entering.");
    expect(screen.getByText("7 words · 52 characters")).toBeInTheDocument();
    const tools = within(screen.getByRole("toolbar", { name: "Text tools" }));
    expect(
      tools.getAllByRole("button").map((button) => button.ariaLabel),
    ).toEqual([
      "Heading",
      "Bold",
      "Italic",
      "Quote",
      "Bulleted list",
      "Numbered list",
      "Undo",
      "Redo",
      "Find & replace",
    ]);
    expect(screen.getByText("Saved")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save text…" })).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Discard changes" }),
    ).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("saves edited details and shows them straight away", async () => {
    apiClient.updateKnowledgeDocumentDetails.mockResolvedValue({
      ...breathing,
      title: "On the breath",
      tradition: "Buddhism",
    });
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const details = within(
      await screen.findByRole("form", { name: "Details" }),
    );

    const title = details.getByLabelText("Title");
    await userEvent.clear(title);
    await userEvent.type(title, "  On the breath ");
    await userEvent.selectOptions(
      details.getByLabelText("Tradition"),
      "Buddhism",
    );
    await userEvent.click(
      details.getByRole("button", { name: "Save details" }),
    );

    expect(apiClient.updateKnowledgeDocumentDetails).toHaveBeenCalledWith(
      "breathing",
      {
        title: "  On the breath ",
        source: "Owner’s summary",
        tradition: "Buddhism",
      },
    );
    expect(
      await details.findByText(
        "Details saved. Replies use them straight away.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "On the breath", level: 1 }),
    ).toBeInTheDocument();
    expect(details.getByLabelText("Title")).toHaveValue("On the breath");
    expect(
      details.getByRole("button", { name: "Save details" }),
    ).toBeDisabled();
  });

  it("won't save a blank title and shows the backend's reason when refused", async () => {
    apiClient.updateKnowledgeDocumentDetails.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/knowledge-documents/breathing",
        "A document needs a tradition.",
      ),
    );
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const details = within(
      await screen.findByRole("form", { name: "Details" }),
    );
    const save = details.getByRole("button", { name: "Save details" });

    await userEvent.clear(details.getByLabelText("Title"));
    expect(save).toBeDisabled();
    await userEvent.type(details.getByLabelText("Title"), "Breath");
    await userEvent.click(save);

    expect(await details.findByRole("alert")).toHaveTextContent(
      "A document needs a tradition.",
    );
    expect(
      screen.getByRole("heading", { name: "Mindful breathing", level: 1 }),
    ).toBeInTheDocument();
  });

  it("edits the text, reviews the changes and saves it to be re-indexed", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const pending = {
      ...breathing,
      status: "pending" as const,
      text_edited: true,
      text: `Slowly.\n${breathing.text}`,
    };
    apiClient.saveKnowledgeDocumentText.mockResolvedValue(pending);
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const editor = await screen.findByRole("textbox", {
      name: "Text of Mindful breathing",
    });

    await userEvent.click(editor);
    await userEvent.paste("Slowly.\n");

    expect(editor).toHaveTextContent(/^Slowly.\s*# Mindful breathing/);
    expect(screen.getByText("Unsaved changes")).toBeInTheDocument();
    expect(screen.getByText("8 words · 60 characters")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Save text…" }));

    const review = within(
      screen.getByRole("dialog", { name: "Review changes" }),
    );
    expect(
      review.getByText(/1 word added · 0 words removed/),
    ).toBeInTheDocument();
    expect(review.getByText("Slowly.").tagName).toBe("INS");
    apiClient.getKnowledgeDocument.mockResolvedValue({
      ...pending,
      status: "ready",
    });
    await userEvent.click(
      review.getByRole("button", { name: "Save and re-index" }),
    );

    expect(apiClient.saveKnowledgeDocumentText).toHaveBeenCalledWith(
      "breathing",
      `Slowly.\n${breathing.text}`,
    );
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(
      screen.getByText(
        "Text saved. Zeph uses it once the document is Ready again.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByText("Edited")).toBeInTheDocument();
    expect(screen.getByText("Saved")).toBeInTheDocument();
    expect(screen.getAllByText("Pending").length).toBeGreaterThan(0);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(screen.queryByText("Pending")).toBeNull();
    expect(screen.getAllByText("Ready").length).toBeGreaterThan(0);
  });

  it("formats with the toolbar, undoes it and saves with Ctrl/⌘+S", async () => {
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const editor = await screen.findByRole("textbox", {
      name: "Text of Mindful breathing",
    });
    await userEvent.click(editor);

    await userEvent.click(screen.getByRole("button", { name: "Heading" }));
    expect(editor).toHaveTextContent(/^Mindful breathing/);
    await userEvent.click(screen.getByRole("button", { name: "Undo" }));
    expect(editor).toHaveTextContent(/^# Mindful breathing/);
    await userEvent.click(screen.getByRole("button", { name: "Redo" }));
    expect(editor).toHaveTextContent(/^Mindful breathing/);
    await userEvent.click(screen.getByRole("button", { name: "Bold" }));
    expect(editor).toHaveTextContent(/^\*\*\*\*Mindful breathing/);

    await userEvent.keyboard("{Control>}s{/Control}");

    expect(
      screen.getByRole("dialog", { name: "Review changes" }),
    ).toBeInTheDocument();
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getByText("Unsaved changes")).toBeInTheDocument();
  });

  it("shows the backend's reason when it refuses the text", async () => {
    apiClient.saveKnowledgeDocumentText.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/knowledge-documents/breathing/text",
        "The text can’t be blank.",
      ),
    );
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const editor = await screen.findByRole("textbox", {
      name: "Text of Mindful breathing",
    });
    await userEvent.click(editor);
    await userEvent.paste("x");
    await userEvent.click(screen.getByRole("button", { name: "Save text…" }));

    await userEvent.click(
      screen.getByRole("button", { name: "Save and re-index" }),
    );

    expect(
      await within(screen.getByRole("dialog")).findByRole("alert"),
    ).toHaveTextContent("The text can’t be blank.");
    expect(screen.getByText("Unsaved changes")).toBeInTheDocument();
  });

  it("discards unsaved changes only after confirming", async () => {
    const confirm = vi.spyOn(window, "confirm");
    confirm.mockReturnValueOnce(false).mockReturnValueOnce(true);
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const editor = await screen.findByRole("textbox", {
      name: "Text of Mindful breathing",
    });
    await userEvent.click(editor);
    await userEvent.paste("x");
    const discard = screen.getByRole("button", { name: "Discard changes" });

    await userEvent.click(discard);
    expect(editor).toHaveTextContent(/^x# Mindful/);
    await userEvent.click(discard);

    expect(confirm).toHaveBeenCalledWith("Discard your unsaved text changes?");
    expect(editor).toHaveTextContent(/^# Mindful/);
    expect(screen.getByText("Saved")).toBeInTheDocument();
  });

  it("asks before following a link with unsaved changes", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const editor = await screen.findByRole("textbox", {
      name: "Text of Mindful breathing",
    });
    await userEvent.click(editor);
    await userEvent.paste("x");

    await userEvent.click(screen.getByRole("link", { name: "← Knowledge" }));

    expect(confirm).toHaveBeenCalledWith(
      "You have unsaved text changes. Leave and lose them?",
    );
    expect(screen.getByText("Unsaved changes")).toBeInTheDocument();
  });

  it("replaces an edited document's file after confirming", async () => {
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    apiClient.getKnowledgeDocument.mockResolvedValue({
      ...breathing,
      text_edited: true,
    });
    apiClient.replaceKnowledgeDocumentFile.mockResolvedValue({
      ...breathing,
      file_name: "breathing-v2.pdf",
      file_type: "pdf",
      status: "pending",
      text_edited: false,
      text: null,
    });
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const replace = within(
      await screen.findByRole("form", { name: "Replace file" }),
    );
    expect(screen.getByText("Edited")).toBeInTheDocument();
    expect(
      replace.getByRole("button", { name: "Replace file" }),
    ).toBeDisabled();
    const file = new File(["%PDF"], "breathing-v2.pdf", {
      type: "application/pdf",
    });

    await userEvent.upload(replace.getByLabelText(/choose one/), file);
    expect(replace.getByText("breathing-v2.pdf")).toBeInTheDocument();
    await userEvent.click(
      replace.getByRole("button", { name: "Replace file" }),
    );

    expect(confirm).toHaveBeenCalledWith(
      expect.stringContaining("Replacing the file replaces those edits"),
    );
    expect(apiClient.replaceKnowledgeDocumentFile).toHaveBeenCalledWith(
      "breathing",
      file,
    );
    expect(
      await replace.findByText(
        "Replaced with breathing-v2.pdf. It’s being read and indexed now.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Edited")).toBeNull();
    expect(screen.getByText("PDF · breathing-v2.pdf")).toBeInTheDocument();
    expect(screen.getByText("No text yet")).toBeInTheDocument();
  });

  it("shows the backend's reason when it refuses a replacement file", async () => {
    apiClient.replaceKnowledgeDocumentFile.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/knowledge-documents/breathing/file",
        "The file is empty.",
      ),
    );
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const replace = within(
      await screen.findByRole("form", { name: "Replace file" }),
    );

    await userEvent.upload(
      replace.getByLabelText(/choose one/),
      new File([""], "empty.txt", { type: "text/plain" }),
    );
    await userEvent.click(
      replace.getByRole("button", { name: "Replace file" }),
    );

    expect(await replace.findByRole("alert")).toHaveTextContent(
      "The file is empty.",
    );
    expect(
      screen.getByText("Markdown · mindful-breathing.md"),
    ).toBeInTheDocument();
  });

  it("previews the text as formatted Markdown", async () => {
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    await screen.findByRole("textbox", { name: "Text of Mindful breathing" });

    await userEvent.click(screen.getByRole("button", { name: "Preview" }));

    const preview = within(screen.getByRole("region", { name: "Preview" }));
    expect(
      preview.getByRole("heading", { name: "Mindful breathing", level: 1 }),
    ).toBeInTheDocument();
    expect(preview.getByText("breath").tagName).toBe("STRONG");
  });

  it("shows the Edited marker when an Admin changed the text", async () => {
    apiClient.getKnowledgeDocument.mockResolvedValue({
      ...breathing,
      text_edited: true,
    });

    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);

    expect(await screen.findByText("Edited")).toBeInTheDocument();
  });

  it("shows why a document failed, with no text, and retries it", async () => {
    apiClient.getKnowledgeDocument.mockResolvedValueOnce(scan);
    apiClient.retryKnowledgeDocument.mockResolvedValue({
      ...scan,
      status: "pending",
      failure_reason: null,
    });
    apiClient.getKnowledgeDocument.mockResolvedValueOnce({
      ...scan,
      status: "pending",
      failure_reason: null,
    });
    renderWithQueries(<KnowledgeDocumentView documentId="scan" />);

    expect(
      await screen.findByText("Scanned PDF — no text found"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/No text could be read from this file/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("textbox", { name: "Text of Being and Time (excerpt)" }),
    ).toHaveTextContent("");

    await userEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(apiClient.retryKnowledgeDocument).toHaveBeenCalledWith("scan");
    expect(await screen.findByText("Pending")).toBeInTheDocument();
    expect(screen.queryByText("Scanned PDF — no text found")).toBeNull();
    expect(screen.getByText("No text yet")).toBeInTheDocument();
  });

  it("checks again while pending until the document is ready", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    apiClient.getKnowledgeDocument.mockResolvedValueOnce({
      ...breathing,
      status: "pending",
      text: null,
    });
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    expect(await screen.findByText("Pending")).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(
      await screen.findByRole("textbox", { name: "Text of Mindful breathing" }),
    ).toBeInTheDocument();
    expect(apiClient.getKnowledgeDocument).toHaveBeenCalledTimes(2);
  });

  it("deletes the document after confirming, then goes back to the list", async () => {
    apiClient.deleteKnowledgeDocument.mockResolvedValue(undefined);
    const confirm = vi.spyOn(window, "confirm");
    confirm.mockReturnValueOnce(false).mockReturnValueOnce(true);
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);
    const remove = await screen.findByRole("button", {
      name: "Delete document",
    });

    await userEvent.click(remove);
    expect(apiClient.deleteKnowledgeDocument).not.toHaveBeenCalled();
    await userEvent.click(remove);

    expect(confirm).toHaveBeenCalledWith(
      "Delete Mindful breathing? Zeph will stop drawing on it.",
    );
    expect(apiClient.deleteKnowledgeDocument).toHaveBeenCalledWith("breathing");
    expect(router.push).toHaveBeenCalledWith("/admin/knowledge");
  });

  it("says when the document no longer exists", async () => {
    apiClient.getKnowledgeDocument.mockRejectedValue(
      new ApiError(404, "/api/admin/knowledge-documents/gone"),
    );

    renderWithQueries(<KnowledgeDocumentView documentId="gone" />);

    expect(
      await screen.findByRole("heading", {
        name: "This document no longer exists",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Back to Knowledge" }),
    ).toHaveAttribute("href", "/admin/knowledge");
  });

  it("offers Try again when the document can't be loaded", async () => {
    apiClient.getKnowledgeDocument
      .mockRejectedValueOnce(
        new ApiError(500, "/api/admin/knowledge-documents"),
      )
      .mockResolvedValueOnce(breathing);
    renderWithQueries(<KnowledgeDocumentView documentId="breathing" />);

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Couldn’t load the document");
    await userEvent.click(
      within(alert).getByRole("button", { name: "Try again" }),
    );

    expect(
      await screen.findByRole("heading", {
        name: "Mindful breathing",
        level: 1,
      }),
    ).toBeInTheDocument();
  });
});
