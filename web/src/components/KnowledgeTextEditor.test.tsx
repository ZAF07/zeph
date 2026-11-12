import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { KnowledgeTextEditor } from "@/components/KnowledgeTextEditor";

const text = [
  "# Mindful breathing",
  "",
  "Notice the **breath** entering.",
  "",
  "<script>alert('x')</script>",
].join("\n");

describe("KnowledgeTextEditor, read-only", () => {
  it("shows the text in a labelled, read-only editor with its length", () => {
    render(<KnowledgeTextEditor value={text} readOnly label="Document text" />);

    const editor = screen.getByRole("textbox", { name: "Document text" });
    expect(editor).toHaveAttribute("aria-readonly", "true");
    expect(editor).toHaveTextContent("Notice the **breath** entering.");
    expect(screen.getByText("8 words · 81 characters")).toBeInTheDocument();
  });

  it("previews the Markdown without running raw HTML", async () => {
    render(<KnowledgeTextEditor value={text} readOnly label="Document text" />);

    await userEvent.click(screen.getByRole("button", { name: "Preview" }));

    const preview = within(screen.getByRole("region", { name: "Preview" }));
    expect(
      preview.getByRole("heading", { name: "Mindful breathing" }),
    ).toBeInTheDocument();
    expect(preview.getByText("breath").tagName).toBe("STRONG");
    expect(document.querySelector("script")).toBeNull();
    expect(screen.getByRole("button", { name: "Preview" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("offers find but no editing controls", () => {
    render(<KnowledgeTextEditor value={text} readOnly label="Document text" />);

    const tools = within(screen.getByRole("toolbar", { name: "Text tools" }));
    expect(
      tools
        .getAllByRole("button")
        .map((button) => button.getAttribute("aria-label")),
    ).toEqual(["Find"]);
    expect(screen.getByRole("button", { name: "Text" })).toBeInTheDocument();
  });
});
