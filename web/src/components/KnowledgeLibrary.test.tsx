import { act, fireEvent, screen, within } from "@testing-library/react";
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

async function findCard(title: string): Promise<ReturnType<typeof within>> {
  fireEvent.click(await screen.findByRole("button", { name: "Expand all" }));
  return within(await screen.findByRole("region", { name: title }));
}

async function expectCount(text: string) {
  expect(
    await screen.findByText(
      (_, element) =>
        element?.tagName === "SPAN" &&
        element.textContent === text &&
        element.children.length === 1,
    ),
  ).toBeInTheDocument();
}

async function openUploadBox(): Promise<ReturnType<typeof within>> {
  await userEvent.click(
    await screen.findByRole("button", { name: "Add a document" }),
  );
  return within(screen.getByRole("region", { name: "Add a document" }));
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

    await expectCount("2 documents · 1 ready · 1 failed");
    const lettersCard = await findCard("Letters to Lucilius");
    expect(
      lettersCard.getByRole("button", { name: /^Letters to Lucilius/ }),
    ).toHaveTextContent("Letters to LuciliusSeneca · StoicismReady2 Oct");
    expect(lettersCard.getByText("PDF")).toBeInTheDocument();
    expect(lettersCard.getByText("letters.pdf")).toBeInTheDocument();
    expect(lettersCard.queryByRole("button", { name: "Retry" })).toBeNull();
    expect(
      lettersCard.getByRole("link", { name: "Open document" }),
    ).toHaveAttribute("href", "/admin/knowledge/letters");
    const beingCard = await findCard("Being and Time (excerpt)");
    expect(beingCard.getByText("Failed")).toBeInTheDocument();
    expect(
      beingCard.getByText("Scanned PDF — no text found"),
    ).toBeInTheDocument();
    expect(
      beingCard.getByRole("button", { name: "Retry" }),
    ).toBeInTheDocument();
  });

  it("uploads a document with its title, source and tradition", async () => {
    apiClient.uploadKnowledgeDocument.mockResolvedValue(notes);
    renderWithQueries(<KnowledgeLibrary />);
    const box = await openUploadBox();
    const upload = box.getByRole("button", { name: "Upload" });
    expect(upload).toBeDisabled();

    const file = await chooseFile("self-compassion.md");
    expect(box.getByText("self-compassion.md")).toBeInTheDocument();
    const title = box.getByLabelText("Title");
    await userEvent.clear(title);
    await userEvent.type(title, "Notes on self-compassion");
    await userEvent.type(box.getByLabelText("Source / author"), "Me");
    await userEvent.selectOptions(
      box.getByLabelText("Tradition"),
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
      (await findCard("Notes on self-compassion")).getByText("Pending"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Add a document" })).toBeNull();
  });

  it("suggests a title from the file name", async () => {
    renderWithQueries(<KnowledgeLibrary />);
    const box = await openUploadBox();

    await chooseFile("tao-te-ching.txt");

    expect(box.getByLabelText("Title")).toHaveValue("tao te ching");
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
    const box = await openUploadBox();

    await chooseFile("huge.txt");
    await userEvent.type(box.getByLabelText("Source / author"), "Me");
    await userEvent.click(box.getByRole("button", { name: "Upload" }));

    expect(await box.findByRole("alert")).toHaveTextContent(
      "The file is bigger than 20 MB.",
    );
  });

  it("retries a failed document", async () => {
    apiClient.retryKnowledgeDocument.mockResolvedValue({
      ...being,
      status: "pending",
      failure_reason: null,
    });
    renderWithQueries(<KnowledgeLibrary />);
    const beingCard = await findCard("Being and Time (excerpt)");
    apiClient.listKnowledgeDocuments.mockResolvedValue([
      letters,
      { ...being, status: "ready", failure_reason: null },
    ]);

    await userEvent.click(beingCard.getByRole("button", { name: "Retry" }));

    expect(apiClient.retryKnowledgeDocument).toHaveBeenCalledWith("being");
    await expectCount("2 documents · 2 ready");
  });

  it("deletes a document after confirming in its card", async () => {
    apiClient.deleteKnowledgeDocument.mockResolvedValue();
    renderWithQueries(<KnowledgeLibrary />);
    const card = await findCard("Letters to Lucilius");
    apiClient.listKnowledgeDocuments.mockResolvedValue([being]);

    await userEvent.click(card.getByRole("button", { name: "Delete" }));
    const confirm = card.getByRole("alertdialog", {
      name: "Delete this document?",
    });
    expect(confirm).toHaveTextContent(
      "Delete “Letters to Lucilius”?Zeph will stop drawing on it.",
    );
    expect(apiClient.deleteKnowledgeDocument).not.toHaveBeenCalled();
    await userEvent.click(
      within(confirm).getByRole("button", { name: "Delete" }),
    );

    expect(apiClient.deleteKnowledgeDocument).toHaveBeenCalledWith("letters");
    expect(
      await screen.findByText("Deleted Letters to Lucilius."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("region", { name: "Letters to Lucilius" }),
    ).toBeNull();
  });

  it("keeps a document when Keep it is chosen", async () => {
    renderWithQueries(<KnowledgeLibrary />);
    const card = await findCard("Letters to Lucilius");

    await userEvent.click(card.getByRole("button", { name: "Delete" }));
    await userEvent.click(card.getByRole("button", { name: "Keep it" }));

    expect(apiClient.deleteKnowledgeDocument).not.toHaveBeenCalled();
    expect(card.queryByRole("alertdialog")).toBeNull();
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

    expect(
      await screen.findByRole("region", { name: "Letters to Lucilius" }),
    ).toBeInTheDocument();
  });
});
