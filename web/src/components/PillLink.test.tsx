import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PillLink } from "@/components/PillLink";

describe("PillLink", () => {
  it("links to the next step, with the arrow hidden from screen readers", () => {
    render(
      <PillLink href="/connect-telegram" label="Connect Telegram" primary />,
    );

    expect(
      screen.getByRole("link", { name: "Connect Telegram" }),
    ).toHaveAttribute("href", "/connect-telegram");
    expect(screen.getByText("→")).toHaveAttribute("aria-hidden", "true");
  });
});
