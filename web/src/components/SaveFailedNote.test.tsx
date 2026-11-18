import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SaveFailedNote } from "@/components/SaveFailedNote";

describe("SaveFailedNote", () => {
  it("announces the failure as an alert", () => {
    render(<SaveFailedNote>Couldn’t save. Try again.</SaveFailedNote>);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "Couldn’t save. Try again.",
    );
  });
});
