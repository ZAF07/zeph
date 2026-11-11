import type { ComponentProps } from "react";
import type { ClerkProvider } from "@clerk/nextjs";

/**
 * Themes Clerk's prebuilt sign-up and sign-in with the design tokens.
 *
 * Colour values mirror the tokens in `globals.css`; element classes use the
 * Tailwind theme directly.
 */
export const clerkAppearance: ComponentProps<
  typeof ClerkProvider
>["appearance"] = {
  variables: {
    colorPrimary: "#0a0a0a",
    colorPrimaryForeground: "#ffffff",
    colorForeground: "#0a0a0a",
    colorMutedForeground: "#525252",
    colorBackground: "#ffffff",
    colorInput: "#ffffff",
    colorInputForeground: "#0a0a0a",
    colorBorder: "#d4d4d4",
    colorDanger: "#c81e1e",
    colorRing: "#1f4fff",
    fontFamily: "var(--font-geist-sans), system-ui, sans-serif",
    fontSize: "15px",
    borderRadius: "10px",
  },
  elements: {
    cardBox:
      "w-full max-w-[420px] rounded-card border border-line shadow-[0_24px_48px_-32px_rgba(0,0,0,0.3)]",
    card: "px-8 pt-9 pb-7 shadow-none",
    headerTitle: "text-[30px] leading-[1.15] font-normal",
    headerSubtitle: "text-sm text-ink-soft",
    socialButtonsBlockButton:
      "min-h-[46px] rounded-full border-line-strong font-medium",
    formFieldInput: "min-h-12 rounded-input border-line-strong text-base",
    formButtonPrimary: "min-h-12 rounded-full bg-ink text-[15px] font-medium",
    footerActionLink: "font-semibold text-blue",
  },
};
