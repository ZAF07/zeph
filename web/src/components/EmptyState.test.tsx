import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmptyState } from "@/components/EmptyState";
import { PillLink } from "@/components/PillLink";

describe("EmptyState", () => {
  it("shows the title, the sentence and the next step", () => {
    render(
      <EmptyState
        title="Nothing remembered yet"
        body="As you talk with Zeph, the details that matter will appear here."
        action={<PillLink href="/memories" label="Talk to Zeph" />}
      />,
    );

    expect(screen.getByText("Nothing remembered yet")).toBeInTheDocument();
    expect(
      screen.getByText(
        "As you talk with Zeph, the details that matter will appear here.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Talk to Zeph" })).toHaveAttribute(
      "href",
      "/memories",
    );
  });
});
