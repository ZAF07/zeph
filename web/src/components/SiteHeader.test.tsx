import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SiteHeader } from "@/components/SiteHeader";

describe("SiteHeader", () => {
  it("shows the nav links, Log in and Get Started", () => {
    render(<SiteHeader />);

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
    render(<SiteHeader />);
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
    render(<SiteHeader />);
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
