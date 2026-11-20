import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EditorLabel } from "@/components/EditorLabel";

describe("EditorLabel", () => {
  it("draws the editor's name and its hint under it, as the form template does", () => {
    render(
      <EditorLabel
        label="Prompt"
        hint="What the Understanding is told to read."
        hintId="prompt-hint"
      />,
    );

    expect(screen.getByText("Prompt")).toHaveClass(
      "text-[15px]",
      "font-normal",
      "text-text",
    );
    const hint = screen.getByText("What the Understanding is told to read.");
    expect(hint).toHaveClass("max-w-[640px]", "text-[13px]", "text-soft");
    expect(hint).toHaveAttribute("id", "prompt-hint");
  });
});
