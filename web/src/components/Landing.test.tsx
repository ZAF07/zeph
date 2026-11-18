import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Landing } from "@/components/Landing";

describe("Landing", () => {
  it("sends every plan's button to sign-up", () => {
    const { container } = render(<Landing />);

    const pricing = within(container.querySelector("#pricing") as HTMLElement);
    for (const name of ["Get Started", "Start Plus", "Start Pro"]) {
      expect(pricing.getByRole("link", { name })).toHaveAttribute(
        "href",
        "/sign-up",
      );
    }
  });

  it("keeps each FAQ answer folded inside its question", () => {
    const { container } = render(<Landing />);

    const questions = container.querySelectorAll("#faq details");
    expect(questions).toHaveLength(5);
    expect(questions[0]).not.toHaveAttribute("open");
    expect(questions[0].querySelector("summary")).toHaveTextContent(
      "What is Zeph?",
    );
    expect(questions[4]).toHaveTextContent("[YOUR CANCELLATION POLICY]");
  });

  it("links the footer's Product column to the site's pages", () => {
    render(<Landing />);

    const footer = within(screen.getByRole("contentinfo"));
    expect(footer.getByRole("link", { name: "How It Works" })).toHaveAttribute(
      "href",
      "/how-it-works",
    );
    expect(footer.getByRole("link", { name: "FAQ" })).toHaveAttribute(
      "href",
      "/#faq",
    );
    expect(footer.getByText(/© 2026 Zeph/)).toBeInTheDocument();
  });
});
