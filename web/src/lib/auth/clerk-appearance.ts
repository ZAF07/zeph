import type { ComponentProps } from "react";
import type { ClerkProvider } from "@clerk/nextjs";

/**
 * The design tokens Clerk needs, as plain values: Clerk works out its own
 * shades from them, so it can't take CSS variables. They mirror
 * `design/tokens.css`.
 */
const tokenColors = {
  bgDeep: "#071922",
  inputBg: "rgba(7,25,34,.6)",
  line: "#2a5263",
  lineStrong: "#5b8b96",
  cream: "#f3e8d6",
  text: "#eaf2f3",
  soft: "#bdd0d5",
  mute: "#9db6be",
  ink: "#0b2a3c",
  danger: "#f4a48c",
};

/**
 * A 1px border in place of the box-shadow outline Clerk draws. Clerk's own
 * rules for these are stronger than ours, so both are `!important`.
 *
 * @param color - The border colour.
 * @returns The style values for a Clerk element.
 */
function outlined(color: string) {
  return {
    border: `1px solid ${color} !important`,
    boxShadow: "none !important",
  };
}

/**
 * Themes Clerk's prebuilt sign-up and sign-in to match the card in the
 * design's `Login` and `Signup` files.
 *
 * Clerk sits flush inside `AuthLayout`'s card, which draws the card itself.
 * Element styles are style objects, not Tailwind classes, because Clerk's own
 * styles sit outside Tailwind's layers and would win over its classes.
 */
export const clerkAppearance: ComponentProps<
  typeof ClerkProvider
>["appearance"] = {
  options: {
    elevation: "flush",
    logoPlacement: "none",
  },
  variables: {
    colorPrimary: tokenColors.cream,
    colorPrimaryForeground: tokenColors.ink,
    colorForeground: tokenColors.text,
    colorMutedForeground: tokenColors.soft,
    colorNeutral: tokenColors.text,
    colorBackground: tokenColors.bgDeep,
    colorInput: tokenColors.inputBg,
    colorInputForeground: tokenColors.text,
    colorBorder: tokenColors.lineStrong,
    colorDanger: tokenColors.danger,
    colorRing: tokenColors.cream,
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
      color: tokenColors.cream,
    },
    headerSubtitle: {
      margin: 0,
      fontSize: "14px",
      lineHeight: 1.55,
      fontWeight: 300,
      color: tokenColors.soft,
    },
    main: { gap: "18px" },
    socialButtonsBlockButton: {
      ...outlined(tokenColors.soft),
      minHeight: "44px",
      borderRadius: "999px",
      background: "transparent",
      color: tokenColors.text,
    },
    socialButtonsBlockButtonText: { fontSize: "14px", fontWeight: 500 },
    dividerLine: { background: tokenColors.line },
    dividerText: { fontSize: "13px", color: tokenColors.soft },
    form: { gap: "18px" },
    formFieldRow: { gap: "6px" },
    formFieldLabel: {
      fontSize: "13px",
      fontWeight: 400,
      color: tokenColors.soft,
    },
    formFieldAction: {
      fontSize: "13px",
      fontWeight: 300,
      color: tokenColors.text,
    },
    formFieldInput: {
      ...outlined(tokenColors.lineStrong),
      minHeight: "46px",
      boxSizing: "border-box",
      padding: "0 14px",
      borderRadius: "10px",
      background: tokenColors.inputBg,
      color: tokenColors.text,
      fontSize: "15px",
      "&::placeholder": { color: tokenColors.mute },
    },
    otpCodeFieldInput: {
      ...outlined(tokenColors.lineStrong),
      color: tokenColors.text,
    },
    formFieldHintText: { fontSize: "12px", color: tokenColors.soft },
    formButtonPrimary: {
      ...outlined(tokenColors.cream),
      minHeight: "44px",
      borderRadius: "999px",
      background: tokenColors.cream,
      color: tokenColors.ink,
      fontSize: "14px",
      fontWeight: 500,
      "&:hover, &:focus, &:active": { background: tokenColors.cream },
    },
    footer: {
      marginTop: "18px",
      gap: "12px",
      background: "transparent",
      padding: 0,
    },
    footerAction: { justifyContent: "center", padding: 0 },
    footerActionText: {
      fontSize: "13px",
      fontWeight: 300,
      color: tokenColors.soft,
    },
    footerActionLink: {
      fontSize: "13px",
      fontWeight: 300,
      color: tokenColors.soft,
      textDecoration: "underline",
      "&:hover": { color: tokenColors.cream },
    },
  },
};
