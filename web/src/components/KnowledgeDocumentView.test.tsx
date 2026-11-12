import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgeDocumentView } from "@/components/KnowledgeDocumentView";
import {
  ApiError,
  type ApiClient,
  type KnowledgeDocumentWithText,
} from "@/lib/api-client";

const apiClient = {
  getKnowledgeDocument: vi.fn<ApiClient["getKnowledgeDocument"]>(),
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

  it("shows the document's details and its text, read-only", async () => {
    render(<KnowledgeDocumentView documentId="breathing" />);

    expect(
      await screen.findByRole("heading", {
        name: "Mindful breathing",
        level: 1,
      }),
    ).toBeInTheDocument();
    expect(apiClient.getKnowledgeDocument).toHaveBeenCalledWith("breathing");
    const details = within(screen.getByRole("region", { name: "Details" }));
    expect(details.getByText("Owner’s summary")).toBeInTheDocument();
    expect(details.getByText("Mindfulness")).toBeInTheDocument();
    expect(
      details.getByText("Markdown · mindful-breathing.md"),
    ).toBeInTheDocument();
    expect(details.getByText("2 Oct 2026")).toBeInTheDocument();
    expect(screen.getAllByText("Ready").length).toBeGreaterThan(0);
    expect(screen.queryByText("Edited")).toBeNull();
    const editor = screen.getByRole("textbox", {
      name: "Text of Mindful breathing",
    });
    expect(editor).toHaveAttribute("aria-readonly", "true");
    expect(editor).toHaveTextContent("Notice the **breath** entering.");
    expect(screen.getByText("7 words · 52 characters")).toBeInTheDocument();
    const tools = within(screen.getByRole("toolbar", { name: "Text tools" }));
    expect(tools.getAllByRole("button")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("previews the text as formatted Markdown", async () => {
    render(<KnowledgeDocumentView documentId="breathing" />);
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

    render(<KnowledgeDocumentView documentId="breathing" />);

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
    render(<KnowledgeDocumentView documentId="scan" />);

    expect(
      await screen.findByText("Scanned PDF — no text found"),
    ).toBeInTheDocument();
    expect(screen.getByText("No text yet")).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).toBeNull();

    await userEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(apiClient.retryKnowledgeDocument).toHaveBeenCalledWith("scan");
    expect(await screen.findByText("Pending")).toBeInTheDocument();
    expect(screen.queryByText("Scanned PDF — no text found")).toBeNull();
  });

  it("checks again while pending until the document is ready", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    apiClient.getKnowledgeDocument.mockResolvedValueOnce({
      ...breathing,
      status: "pending",
      text: null,
    });
    render(<KnowledgeDocumentView documentId="breathing" />);
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
    render(<KnowledgeDocumentView documentId="breathing" />);
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

    render(<KnowledgeDocumentView documentId="gone" />);

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
    render(<KnowledgeDocumentView documentId="breathing" />);

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
