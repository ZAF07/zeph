import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Pricing } from "@/components/Pricing";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";

describe("Pricing", () => {
  it("shows only Copy text, header and footer included", () => {
    const { container } = render(<Pricing copy={markedCopy()} />);

    expect(wordsNotFromCopy(container)).toEqual([]);
    expect(
      screen.getByRole("heading", { level: 3, name: "⟦pricing.plus.name⟧" }),
    ).toBeInTheDocument();
  });

  it("shows the three plans, each signing up", () => {
    const { container } = render(<Pricing copy={seedCopy()} />);

    const pricing = within(container.querySelector("#pricing") as HTMLElement);
    for (const plan of ["Free", "Plus", "Pro"]) {
      expect(
        pricing.getByRole("heading", { level: 3, name: plan }),
      ).toBeInTheDocument();
    }
    expect(pricing.getByRole("link", { name: "Start Plus" })).toHaveAttribute(
      "href",
      "/sign-up",
    );
  });

  it("sits between the site header and footer", () => {
    render(<Pricing copy={seedCopy()} />);

    expect(screen.getByRole("link", { name: "Zeph home" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(
      within(screen.getByRole("contentinfo")).getByRole("link", {
        name: "Pricing",
      }),
    ).toHaveAttribute("href", "/pricing");
  });
});
