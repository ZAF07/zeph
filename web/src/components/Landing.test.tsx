import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Landing } from "@/components/Landing";
import {
  markedCopy,
  seedCopy,
  wordsNotFromCopy,
  withoutMarkedCopy,
} from "@/test/copy";

describe("Landing", () => {
  it("shows only Copy text in every section, header and footer included; icons aside, it has no words of its own", () => {
    const { container } = render(<Landing copy={markedCopy()} />);

    const sections = container.querySelectorAll("section");
    expect(sections).toHaveLength(5);
    for (const section of sections) {
      const words = section.cloneNode(true) as HTMLElement;
      words
        .querySelectorAll("[aria-hidden='true']")
        .forEach((icon) => icon.remove());
      expect(withoutMarkedCopy(words.textContent ?? "")).toBe("");
    }
    expect(wordsNotFromCopy(container)).toEqual([]);
    expect(screen.getByRole("heading", { level: 1 }).textContent?.trim()).toBe(
      "⟦landing.hero.heading_first_line⟧ ⟦landing.hero.heading_second_line⟧",
    );
  });

  it("shows an Admin's changed main heading", () => {
    const copy = {
      ...seedCopy(),
      "landing.hero.heading_first_line": "Think Slower,",
    };

    render(<Landing copy={copy} />);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Think Slower, Live More Deliberately.",
      }),
    ).toBeInTheDocument();
  });

  it("sends every plan's button to sign-up", () => {
    const { container } = render(<Landing copy={seedCopy()} />);

    const pricing = within(container.querySelector("#pricing") as HTMLElement);
    for (const name of ["Get Started", "Start Plus", "Start Pro"]) {
      expect(pricing.getByRole("link", { name })).toHaveAttribute(
        "href",
        "/sign-up",
      );
    }
  });

  it("keeps each FAQ answer folded inside its question", () => {
    const { container } = render(<Landing copy={seedCopy()} />);

    const questions = container.querySelectorAll("#faq details");
    expect(questions).toHaveLength(5);
    expect(questions[0]).not.toHaveAttribute("open");
    expect(questions[0].querySelector("summary")).toHaveTextContent(
      "What is Zeph?",
    );
    expect(questions[4]).toHaveTextContent("[YOUR CANCELLATION POLICY]");
  });

  it("links the footer's Product column to the site's pages", () => {
    render(<Landing copy={seedCopy()} />);

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

  it("shows an Admin's changed footer copyright", () => {
    const copy = { ...seedCopy(), "shared.footer.copyright": "© 2027 Zeph" };

    render(<Landing copy={copy} />);

    expect(
      within(screen.getByRole("contentinfo")).getByText("© 2027 Zeph"),
    ).toBeInTheDocument();
  });
});
