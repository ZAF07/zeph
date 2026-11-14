import { act, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { KnowledgeLibrary } from "@/components/KnowledgeLibrary";
import {
  ApiError,
  type ApiClient,
  type KnowledgeDocument,
} from "@/lib/api-client";
import { renderWithQueries } from "@/test/render-with-queries";

const apiClient = {
  listKnowledgeDocuments: vi.fn<ApiClient["listKnowledgeDocuments"]>(),
  uploadKnowledgeDocument: vi.fn<ApiClient["uploadKnowledgeDocument"]>(),
  retryKnowledgeDocument: vi.fn<ApiClient["retryKnowledgeDocument"]>(),
  deleteKnowledgeDocument: vi.fn<ApiClient["deleteKnowledgeDocument"]>(),
};

vi.mock("@/lib/use-api-client", () => ({
  useApiClient: () => apiClient,
}));

function knowledgeDocument(
  id: string,
  title: string,
  overrides: Partial<KnowledgeDocument> = {},
): KnowledgeDocument {
  return {
    id,
    title,
    source: "Seneca",
    tradition: "Stoicism",
    file_name: `${id}.pdf`,
    file_type: "pdf",
    status: "ready",
    failure_reason: null,
    text_edited: false,
    created_at: "2026-10-02T09:00:00Z",
    when_it_helps: "",
    ...overrides,
  };
}

const letters = knowledgeDocument("letters", "Letters to Lucilius");
const notes = knowledgeDocument("notes", "Notes on self-compassion", {
  source: "Owner’s summary",
  tradition: "Psychology",
  file_type: "markdown",
  status: "pending",
});
const being = knowledgeDocument("being", "Being and Time (excerpt)", {
  source: "Heidegger",
  tradition: "Existentialism",
  status: "failed",
  failure_reason: "Scanned PDF — no text found",
});

function rowFor(title: string): ReturnType<typeof within> {
  const row = screen.getByText(title).closest("tr");
  if (!row) {
    throw new Error(`No row for ${title}`);
  }
  return within(row);
}

async function chooseFile(name: string): Promise<File> {
  const file = new File(["Notice the breath."], name, { type: "text/plain" });
  await userEvent.upload(screen.getByLabelText(/choose one/), file);
  return file;
}

describe("KnowledgeLibrary", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    apiClient.listKnowledgeDocuments.mockResolvedValue([letters, being]);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("lists documents with their type, status and why one failed", async () => {
    renderWithQueries(<KnowledgeLibrary />);

    await screen.findByText("Letters to Lucilius");
    expect(
      screen.getByText("2 documents · 1 ready · 1 failed"),
    ).toBeInTheDocument();
    const lettersRow = rowFor("Letters to Lucilius");
    expect(lettersRow.getByText("Seneca")).toBeInTheDocument();
    expect(lettersRow.getByText("Stoicism")).toBeInTheDocument();
    expect(lettersRow.getByText("PDF")).toBeInTheDocument();
    expect(lettersRow.getByText("Ready")).toBeInTheDocument();
    expect(lettersRow.getByText("2 Oct")).toBeInTheDocument();
    expect(lettersRow.queryByRole("button", { name: "Retry" })).toBeNull();
    expect(
      lettersRow.getByRole("link", { name: "Letters to Lucilius" }),
    ).toHaveAttribute("href", "/admin/knowledge/letters");
    const beingRow = rowFor("Being and Time (excerpt)");
    expect(beingRow.getByText("Failed")).toBeInTheDocument();
    expect(
      beingRow.getByText("Scanned PDF — no text found"),
    ).toBeInTheDocument();
    expect(beingRow.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });

  it("uploads a document with its title, source and tradition", async () => {
    apiClient.uploadKnowledgeDocument.mockResolvedValue(notes);
    renderWithQueries(<KnowledgeLibrary />);
    await screen.findByText("Letters to Lucilius");
    const upload = screen.getByRole("button", { name: "Upload" });
    expect(upload).toBeDisabled();

    const file = await chooseFile("self-compassion.md");
    expect(screen.getByText("self-compassion.md")).toBeInTheDocument();
    const title = screen.getByLabelText("Title");
    await userEvent.clear(title);
    await userEvent.type(title, "Notes on self-compassion");
    await userEvent.type(screen.getByLabelText("Source / author"), "Me");
    await userEvent.selectOptions(
      screen.getByLabelText("Tradition"),
      "Psychology",
    );
    apiClient.listKnowledgeDocuments.mockResolvedValue([notes, letters, being]);
    await userEvent.click(upload);

    expect(apiClient.uploadKnowledgeDocument).toHaveBeenCalledWith({
      file,
      title: "Notes on self-compassion",
      source: "Me",
      tradition: "Psychology",
    });
    expect(
      await screen.findByText(
        "Uploaded Notes on self-compassion. It’s being indexed now.",
      ),
    ).toBeInTheDocument();
    expect(
      rowFor("Notes on self-compassion").getByText("Pending"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Title")).toHaveValue("");
  });

  it("suggests a title from the file name", async () => {
    renderWithQueries(<KnowledgeLibrary />);
    await screen.findByText("Letters to Lucilius");

    await chooseFile("tao-te-ching.txt");

    expect(screen.getByLabelText("Title")).toHaveValue("tao te ching");
  });

  it("shows why the backend refused an upload", async () => {
    apiClient.uploadKnowledgeDocument.mockRejectedValue(
      new ApiError(
        422,
        "/api/admin/knowledge-documents",
        "The file is bigger than 20 MB.",
      ),
    );
    renderWithQueries(<KnowledgeLibrary />);
    await screen.findByText("Letters to Lucilius");

    await chooseFile("huge.txt");
    await userEvent.type(screen.getByLabelText("Source / author"), "Me");
    await userEvent.click(screen.getByRole("button", { name: "Upload" }));

    expect(
      await screen.findByText("The file is bigger than 20 MB."),
    ).toBeInTheDocument();
  });

  it("retries a failed document", async () => {
    apiClient.retryKnowledgeDocument.mockResolvedValue({
      ...being,
      status: "pending",
      failure_reason: null,
    });
    renderWithQueries(<KnowledgeLibrary />);
    await screen.findByText("Being and Time (excerpt)");
    apiClient.listKnowledgeDocuments.mockResolvedValue([
      letters,
      { ...being, status: "ready", failure_reason: null },
    ]);

    await userEvent.click(
      rowFor("Being and Time (excerpt)").getByRole("button", { name: "Retry" }),
    );

    expect(apiClient.retryKnowledgeDocument).toHaveBeenCalledWith("being");
    expect(
      await screen.findByText("2 documents · 2 ready"),
    ).toBeInTheDocument();
  });

  it("deletes a document after confirming", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    apiClient.deleteKnowledgeDocument.mockResolvedValue();
    renderWithQueries(<KnowledgeLibrary />);
    await screen.findByText("Letters to Lucilius");
    apiClient.listKnowledgeDocuments.mockResolvedValue([being]);

    await userEvent.click(
      screen.getByRole("button", { name: "Delete Letters to Lucilius" }),
    );

    expect(window.confirm).toHaveBeenCalledWith(
      "Delete Letters to Lucilius? Zeph will stop drawing on it.",
    );
    expect(apiClient.deleteKnowledgeDocument).toHaveBeenCalledWith("letters");
    expect(
      await screen.findByText("Deleted Letters to Lucilius."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Seneca")).toBeNull();
  });

  it("keeps a document when deleting is not confirmed", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(false);
    renderWithQueries(<KnowledgeLibrary />);
    await screen.findByText("Letters to Lucilius");

    await userEvent.click(
      screen.getByRole("button", { name: "Delete Letters to Lucilius" }),
    );

    expect(apiClient.deleteKnowledgeDocument).not.toHaveBeenCalled();
  });

  it("checks again while a document is pending until it is ready", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    apiClient.listKnowledgeDocuments.mockResolvedValue([notes]);
    renderWithQueries(<KnowledgeLibrary />);
    await screen.findByText("Pending");
    apiClient.listKnowledgeDocuments.mockResolvedValue([
      { ...notes, status: "ready" },
    ]);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });

    expect(await screen.findByText("Ready")).toBeInTheDocument();
    const callsWhenReady = apiClient.listKnowledgeDocuments.mock.calls.length;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(9000);
    });
    expect(apiClient.listKnowledgeDocuments).toHaveBeenCalledTimes(
      callsWhenReady,
    );
  });

  it("explains an empty library", async () => {
    apiClient.listKnowledgeDocuments.mockResolvedValue([]);
    renderWithQueries(<KnowledgeLibrary />);

    expect(await screen.findByText("The library is empty")).toBeInTheDocument();
    expect(
      screen.getByText(/Zeph relies on general knowledge only/),
    ).toBeInTheDocument();
  });

  it("shows an error with Try again when the list can't load", async () => {
    apiClient.listKnowledgeDocuments.mockRejectedValueOnce(new Error("down"));
    renderWithQueries(<KnowledgeLibrary />);

    expect(
      await screen.findByText("Couldn’t load the document list"),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));

    expect(await screen.findByText("Letters to Lucilius")).toBeInTheDocument();
  });
});
