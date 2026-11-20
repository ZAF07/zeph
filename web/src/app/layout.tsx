import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import type { ReactNode } from "react";

import "@/app/globals.css";
import { AuthProvider } from "@/lib/auth/AuthProvider";
import { QueryProvider } from "@/lib/QueryProvider";

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  fallback: ["system-ui", "sans-serif"],
  adjustFontFallback: false,
});

export const metadata: Metadata = {
  title: "Zeph",
  description: "Your Zeph Dashboard",
};

/**
 * The root layout: fonts, global styles, sign-in and the shared cache of
 * backend data.
 *
 * @param props - `children` is the page.
 * @returns The HTML document.
 */
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <html lang="en" className={outfit.variable}>
        <body>
          <QueryProvider>{children}</QueryProvider>
        </body>
      </html>
    </AuthProvider>
  );
}
