import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AuthLayout } from "@/components/AuthLayout";

function renderSignInLayout() {
  return render(
    <AuthLayout
      eyebrow="Welcome back"
      switchPrompt="New to Zeph?"
      switchLink={{ href: "/sign-up", label: "Sign up" }}
    >
      <form aria-label="Clerk form" />
    </AuthLayout>,
  );
}

describe("AuthLayout", () => {
  it("offers the other auth page in the header", () => {
    renderSignInLayout();

    expect(screen.getByText("New to Zeph?")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign up" })).toHaveAttribute(
      "href",
      "/sign-up",
    );
  });

  it("puts the eyebrow and the Clerk form inside the card", () => {
    const { container } = renderSignInLayout();

    const card = container.querySelector("[data-clerk-card]");
    expect(card).toHaveTextContent("Welcome back");
    expect(card).toContainElement(
      screen.getByRole("form", { name: "Clerk form" }),
    );
  });

  it("shows the Terms, 18+ and AI companion lines", () => {
    renderSignInLayout();

    expect(screen.getByRole("link", { name: "Terms" })).toHaveAttribute(
      "href",
      "/terms",
    );
    expect(
      screen.getByRole("link", { name: "Privacy policy" }),
    ).toHaveAttribute("href", "/privacy");
    expect(
      screen.getByText(/You must be 18 or older to use Zeph/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Zeph is an AI companion\. It isn’t a mental-health/),
    ).toBeInTheDocument();
  });
});
