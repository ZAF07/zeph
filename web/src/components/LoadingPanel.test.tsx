import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LoadingPanel } from "@/components/LoadingPanel";

describe("LoadingPanel", () => {
  it.each(["banner", "card"] as const)(
    "tells screen readers what is loading, as a %s",
    (shape) => {
      render(<LoadingPanel shape={shape} label="Loading memories" />);

      expect(
        screen.getByRole("status", { name: "Loading memories" }),
      ).toBeInTheDocument();
    },
  );
});
