import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HowItWorks } from "@/components/HowItWorks";

describe("HowItWorks", () => {
  it("lists the five steps in order", () => {
    render(<HowItWorks />);

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

  it("offers sign-up and pricing at the foot", () => {
    render(<HowItWorks />);

    expect(
      screen.getByRole("link", { name: /Get Started Free/ }),
    ).toHaveAttribute("href", "/sign-up");
    expect(screen.getByRole("link", { name: "See pricing" })).toHaveAttribute(
      "href",
      "/#pricing",
    );
  });
});
