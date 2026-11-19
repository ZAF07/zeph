import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HowItWorks } from "@/components/HowItWorks";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";

describe("HowItWorks", () => {
  it("shows only Copy text, header and footer included", () => {
    const { container } = render(<HowItWorks copy={markedCopy()} />);

    expect(wordsNotFromCopy(container)).toEqual([]);
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe(
      "⟦how_it_works.hero.heading_first_line⟧⟦how_it_works.hero.heading_second_line⟧",
    );
    expect(screen.getByRole("contentinfo")).toHaveTextContent(
      "⟦shared.footer.copyright⟧",
    );
  });

  it("lists the five steps in order", () => {
    render(<HowItWorks copy={seedCopy()} />);

    const steps = screen
      .getAllByRole("heading", { level: 3 })
      .slice(0, 5)
      .map((heading) => heading.textContent);
    expect(steps).toEqual([
      "Create your account",
      "Connect Telegram",
      "Talk it through",
      "It remembers, with your permission",
      "It checks in, if you want it to",
    ]);
  });

  it("shows an Admin's changed step title", () => {
    const copy = {
      ...seedCopy(),
      "how_it_works.steps.step_3.title": "Just talk",
    };

    render(<HowItWorks copy={copy} />);

    expect(
      screen.getByRole("heading", { level: 3, name: "Just talk" }),
    ).toBeInTheDocument();
  });

  it("offers sign-up and pricing at the foot", () => {
    render(<HowItWorks copy={seedCopy()} />);

    expect(
      screen.getByRole("link", { name: /Get Started Free/ }),
    ).toHaveAttribute("href", "/sign-up");
    expect(screen.getByRole("link", { name: "See pricing" })).toHaveAttribute(
      "href",
      "/pricing",
    );
  });
});
