import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SavedNote } from "@/components/SavedNote";

describe("SavedNote", () => {
  it("announces the save politely", () => {
    render(<SavedNote>Saved.</SavedNote>);

    expect(screen.getByRole("status")).toHaveTextContent("Saved.");
  });
});
