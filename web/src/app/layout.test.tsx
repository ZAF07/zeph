import type { ReactNode } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/app/globals.css", () => ({}));

vi.mock("next/font/google", () => ({
  Outfit: () => ({ variable: "outfit-font-variable" }),
}));

vi.mock("@/lib/auth/AuthProvider", () => ({
  AuthProvider: ({ children }: { children: ReactNode }) => children,
}));

vi.mock("@/lib/QueryProvider", () => ({
  QueryProvider: ({ children }: { children: ReactNode }) => children,
}));

const { default: RootLayout } = await import("@/app/layout");

describe("RootLayout", () => {
  it("sets the Outfit variable on <html>, where the theme's font is worked out", () => {
    const markup = renderToStaticMarkup(<RootLayout>page</RootLayout>);

    expect(markup).toMatch(/<html[^>]*class="outfit-font-variable"/);
  });
});
