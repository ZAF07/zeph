import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ToBuildTag } from "@/components/ToBuildTag";

describe("ToBuildTag", () => {
  it("reads To build", () => {
    render(<ToBuildTag />);

    expect(screen.getByText("To build")).toBeInTheDocument();
  });
});
