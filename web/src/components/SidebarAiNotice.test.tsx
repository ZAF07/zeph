import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SidebarAiNotice } from "@/components/SidebarAiNotice";

describe("SidebarAiNotice", () => {
  it("shows the short AI notice from Copy", () => {
    render(
      <SidebarAiNotice
        copy={{ "shared.dashboard.ai_notice": "Edited: Zeph is an AI." }}
      />,
    );

    expect(screen.getByText("Edited: Zeph is an AI.")).toBeInTheDocument();
  });
});
