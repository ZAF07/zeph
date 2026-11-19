import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { siteHeaderWords } from "@/components/site-links";
import { SiteHeader } from "@/components/SiteHeader";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";

describe("SiteHeader", () => {
  it("shows only Copy words, with the menu open or closed", () => {
    const { container } = render(
      <SiteHeader words={siteHeaderWords(markedCopy())} />,
    );
    expect(wordsNotFromCopy(container)).toEqual([]);

    fireEvent.click(
      screen.getByRole("button", { name: "⟦shared.header.open_menu⟧" }),
    );

    expect(wordsNotFromCopy(container)).toEqual([]);
    expect(
      screen.getByRole("navigation", { name: "⟦shared.header.menu_label⟧" }),
    ).toBeInTheDocument();
  });

  it("shows an Admin's changed log-in link in the bar and the phone menu", () => {
    const copy = { ...seedCopy(), "shared.header.log_in": "Sign in" };
    render(<SiteHeader words={siteHeaderWords(copy)} />);

    fireEvent.click(screen.getByRole("button", { name: "Open the menu" }));

    expect(screen.getAllByRole("link", { name: "Sign in" })).toHaveLength(2);
  });

  it("shows the nav links, Log in and Get Started", () => {
    render(<SiteHeader words={siteHeaderWords(seedCopy())} />);

    expect(screen.getByRole("link", { name: "How It Works" })).toHaveAttribute(
      "href",
      "/how-it-works",
    );
    expect(screen.getByRole("link", { name: "Pricing" })).toHaveAttribute(
      "href",
      "/pricing",
    );
    expect(screen.getByRole("link", { name: "Log in" })).toHaveAttribute(
      "href",
      "/sign-in",
    );
    expect(screen.getByRole("link", { name: /Get Started/ })).toHaveAttribute(
      "href",
      "/sign-up",
    );
  });

  it("opens the phone nav panel from the menu button, with Log in last", () => {
    render(<SiteHeader words={siteHeaderWords(seedCopy())} />);
    expect(
      screen.queryByRole("navigation", { name: "Site" }),
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Open the menu" }));

    const panel = screen.getByRole("navigation", { name: "Site" });
    const labels = Array.from(panel.querySelectorAll("a")).map(
      (link) => link.textContent,
    );
    expect(labels).toEqual([
      "How It Works",
      "Conversations",
      "Pricing",
      "FAQ",
      "Log in",
    ]);
    expect(
      screen.getByRole("button", { name: "Close the menu" }),
    ).toHaveAttribute("aria-expanded", "true");
  });

  it("closes the panel when a link in it is chosen", () => {
    render(<SiteHeader words={siteHeaderWords(seedCopy())} />);
    fireEvent.click(screen.getByRole("button", { name: "Open the menu" }));

    const panel = screen.getByRole("navigation", { name: "Site" });
    fireEvent.click(panel.querySelector("a[href='/#faq']") as Element);

    expect(
      screen.queryByRole("navigation", { name: "Site" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Open the menu" }),
    ).toHaveAttribute("aria-expanded", "false");
  });
});
