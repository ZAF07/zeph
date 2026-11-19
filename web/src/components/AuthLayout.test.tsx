import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AuthLayout } from "@/components/AuthLayout";
import type { Copy } from "@/lib/copy";
import { markedCopy, seedCopy, wordsNotFromCopy } from "@/test/copy";

function renderLayout(page: "sign_in" | "sign_up", copy: Copy = seedCopy()) {
  return render(
    <AuthLayout copy={copy} page={page}>
      <form aria-label="Clerk form" />
    </AuthLayout>,
  );
}

describe("AuthLayout", () => {
  it("offers the other auth page in the header", () => {
    renderLayout("sign_in");

    expect(screen.getByText("New to Zeph?")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign up" })).toHaveAttribute(
      "href",
      "/sign-up",
    );
  });

  it("offers sign-in from the sign-up page", () => {
    renderLayout("sign_up");

    expect(screen.getByText("Have an account?")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/sign-in",
    );
  });

  it("puts the eyebrow and the Clerk form inside the card", () => {
    const { container } = renderLayout("sign_in");

    const card = container.querySelector("[data-clerk-card]");
    expect(card).toHaveTextContent("Welcome back");
    expect(card).toContainElement(
      screen.getByRole("form", { name: "Clerk form" }),
    );
  });

  it("shows the Terms, 18+ and AI companion lines", () => {
    renderLayout("sign_in");

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

  it.each(["sign_in", "sign_up"] as const)(
    "shows only Copy text around the Clerk form on %s, screen-reader labels included",
    (page) => {
      const { container } = renderLayout(page, markedCopy());

      const ourWords = container.cloneNode(true) as HTMLElement;
      ourWords.querySelector("form[aria-label='Clerk form']")?.remove();
      expect(wordsNotFromCopy(ourWords)).toEqual([]);
      expect(container).toHaveTextContent(`⟦auth.${page}.eyebrow⟧`);
      expect(
        screen.getByRole("link", { name: "⟦shared.header.home_link_label⟧" }),
      ).toHaveTextContent("⟦shared.wordmark⟧");
    },
  );

  it("keeps both links where an Admin moved them in the Terms line", () => {
    renderLayout("sign_up", {
      ...seedCopy(),
      "auth.terms_line": "Read our {privacy} and {terms} first.",
      "auth.terms_link": "terms of use",
    });

    expect(screen.getByText(/Read our/)).toHaveTextContent(
      "Read our Privacy policy and terms of use first.",
    );
    expect(screen.getByRole("link", { name: "terms of use" })).toHaveAttribute(
      "href",
      "/terms",
    );
  });
});
