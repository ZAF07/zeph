import type { ComponentProps } from "react";
import type { ClerkProvider } from "@clerk/nextjs";

/**
 * Themes Clerk's prebuilt sign-up and sign-in to match the card in the
 * design's `Login` and `Signup` files.
 *
 * Clerk sits flush inside `AuthLayout`'s card, which draws the card itself.
 * Colour values mirror the tokens in `design/tokens.css`. Element styles are
 * style objects, not Tailwind classes, because Clerk's own styles sit outside
 * Tailwind's layers and would win over its classes. Clerk draws borders as
 * box shadows with stronger rules, so those few values are `!important`.
 */
export const clerkAppearance: ComponentProps<
  typeof ClerkProvider
>["appearance"] = {
  options: {
    elevation: "flush",
    logoPlacement: "none",
  },
  variables: {
    colorPrimary: "#f3e8d6",
    colorPrimaryForeground: "#0b2a3c",
    colorForeground: "#eaf2f3",
    colorMutedForeground: "#bdd0d5",
    colorNeutral: "#eaf2f3",
    colorBackground: "#071922",
    colorInput: "rgba(7,25,34,.6)",
    colorInputForeground: "#eaf2f3",
    colorBorder: "#5b8b96",
    colorDanger: "#f4a48c",
    colorRing: "#f3e8d6",
    colorShadow: "transparent",
    fontFamily: "var(--font-outfit), system-ui, sans-serif",
    fontSize: "14px",
    fontWeight: { normal: 300, medium: 400, semibold: 500, bold: 400 },
    borderRadius: "10px",
  },
  elements: {
    rootBox: { width: "100%", minWidth: 0 },
    cardBox: { width: "100%", minWidth: 0, background: "transparent" },
    card: { minWidth: 0, padding: 0, gap: "18px", background: "transparent" },
    header: {
      minWidth: 0,
      maxWidth: "100%",
      alignItems: "flex-start",
      textAlign: "left",
      gap: "6px",
    },
    identityPreview: { minWidth: 0, maxWidth: "100%" },
    identityPreviewText: {
      minWidth: 0,
      whiteSpace: "normal",
      overflowWrap: "anywhere",
    },
    headerTitle: {
      margin: 0,
      fontSize: "32px",
      lineHeight: 1.15,
      fontWeight: 400,
      color: "#f3e8d6",
    },
    headerSubtitle: {
      margin: 0,
      fontSize: "14px",
      lineHeight: 1.55,
      fontWeight: 300,
      color: "#bdd0d5",
    },
    main: { gap: "18px" },
    socialButtonsBlockButton: {
      minHeight: "44px",
      borderRadius: "999px",
      border: "1px solid #bdd0d5 !important",
      background: "transparent",
      boxShadow: "none !important",
      color: "#eaf2f3",
    },
    socialButtonsBlockButtonText: { fontSize: "14px", fontWeight: 500 },
    dividerLine: { background: "#2a5263" },
    dividerText: { fontSize: "13px", color: "#bdd0d5" },
    form: { gap: "18px" },
    formFieldRow: { gap: "6px" },
    formFieldLabel: { fontSize: "13px", fontWeight: 400, color: "#bdd0d5" },
    formFieldAction: { fontSize: "13px", fontWeight: 300, color: "#eaf2f3" },
    formFieldInput: {
      minHeight: "46px",
      boxSizing: "border-box",
      padding: "0 14px",
      borderRadius: "10px",
      border: "1px solid #5b8b96 !important",
      background: "rgba(7,25,34,.6)",
      boxShadow: "none !important",
      color: "#eaf2f3",
      fontSize: "15px",
      "&::placeholder": { color: "#9db6be" },
    },
    otpCodeFieldInput: {
      border: "1px solid #5b8b96 !important",
      boxShadow: "none !important",
      color: "#eaf2f3",
    },
    formFieldHintText: { fontSize: "12px", color: "#bdd0d5" },
    formButtonPrimary: {
      minHeight: "44px",
      borderRadius: "999px",
      border: "1px solid #f3e8d6 !important",
      background: "#f3e8d6",
      boxShadow: "none !important",
      color: "#0b2a3c",
      fontSize: "14px",
      fontWeight: 500,
      "&:hover, &:focus, &:active": { background: "#f3e8d6" },
    },
    footer: {
      marginTop: "18px",
      gap: "12px",
      background: "transparent",
      padding: 0,
    },
    footerAction: { justifyContent: "center", padding: 0 },
    footerActionText: { fontSize: "13px", fontWeight: 300, color: "#bdd0d5" },
    footerActionLink: {
      fontSize: "13px",
      fontWeight: 300,
      color: "#bdd0d5",
      textDecoration: "underline",
      "&:hover": { color: "#f3e8d6" },
    },
  },
};

/**
 * The copy Clerk shows on the sign-in and sign-up pages, from the design's
 * `Login` and `Signup` files.
 */
export const clerkLocalization: ComponentProps<
  typeof ClerkProvider
>["localization"] = {
  signIn: {
    start: {
      title: "Sign in to Zeph",
      subtitle:
        "Your memories, check-ins and account live here. The conversation itself happens in Telegram.",
    },
  },
  signUp: {
    start: {
      title: "Create your account",
      subtitle:
        "Sign up here, answer a few short questions, then meet Zeph in Telegram.",
    },
  },
  formFieldInputPlaceholder__emailAddress: "you@example.com",
};
