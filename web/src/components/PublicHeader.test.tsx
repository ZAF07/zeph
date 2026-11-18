import { render, screen } from "@testing-library/react";
import Link from "next/link";
import { describe, expect, it } from "vitest";

import { PublicHeader } from "@/components/PublicHeader";

describe("PublicHeader", () => {
  it("shows the Zeph wordmark linking home and the actions", () => {
    render(<PublicHeader actions={<Link href="/sign-up">Sign up</Link>} />);

    expect(screen.getByRole("link", { name: "Zeph home" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(screen.getByRole("link", { name: "Sign up" })).toHaveAttribute(
      "href",
      "/sign-up",
    );
  });

  it("puts the nav links in a nav", () => {
    render(
      <PublicHeader
        nav={<Link href="/how-it-works">How It Works</Link>}
        actions={null}
      />,
    );

    expect(
      screen.getByRole("navigation").querySelector("a[href='/how-it-works']"),
    ).toHaveTextContent("How It Works");
  });
});
