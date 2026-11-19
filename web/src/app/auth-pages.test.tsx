import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Copy } from "@/lib/copy";
import { seedCopy } from "@/test/copy";

const loadCopy = vi.fn<() => Promise<Copy | null>>();

vi.mock("@/lib/server-copy", () => ({ loadCopy }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh: vi.fn() }),
}));

vi.mock("@clerk/nextjs", () => ({
  SignIn: () => <form aria-label="Clerk sign-in" />,
  SignUp: () => <form aria-label="Clerk sign-up" />,
  ClerkProvider: ({ children }: { children: ReactNode }) => children,
}));

const signIn = await import("@/app/sign-in/[[...sign-in]]/page");
const signUp = await import("@/app/sign-up/[[...sign-up]]/page");

describe.each([
  {
    route: "/sign-in",
    page: signIn,
    form: "Clerk sign-in",
    eyebrowKey: "auth.sign_in.eyebrow",
    titleKey: "auth.sign_in.page_title",
    descriptionKey: "auth.sign_in.page_description",
  },
  {
    route: "/sign-up",
    page: signUp,
    form: "Clerk sign-up",
    eyebrowKey: "auth.sign_up.eyebrow",
    titleKey: "auth.sign_up.page_title",
    descriptionKey: "auth.sign_up.page_description",
  },
])(
  "the $route page",
  ({ page, form, eyebrowKey, titleKey, descriptionKey }) => {
    beforeEach(() => {
      loadCopy.mockReset();
      loadCopy.mockResolvedValue(seedCopy());
    });

    it("shows the Clerk form under the eyebrow from Copy", async () => {
      loadCopy.mockResolvedValue({
        ...seedCopy(),
        [eyebrowKey]: "Hello again",
      });

      render(await page.default());

      expect(screen.getByText("Hello again")).toBeInTheDocument();
      expect(screen.getByRole("form", { name: form })).toBeInTheDocument();
    });

    it("takes its tab title and description from Copy", async () => {
      expect(await page.generateMetadata()).toEqual({
        title: seedCopy()[titleKey],
        description: seedCopy()[descriptionKey],
      });
    });

    it("shows the error state when Copy can't be read", async () => {
      loadCopy.mockResolvedValue(null);

      render(await page.default());

      expect(screen.getByRole("alert")).toHaveTextContent(
        "Couldn’t load this page",
      );
      expect(await page.generateMetadata()).toEqual({});
    });
  },
);
