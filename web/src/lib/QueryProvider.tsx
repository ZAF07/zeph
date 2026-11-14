"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { createQueryClient } from "@/lib/query-client";

/**
 * Gives every client component one shared cache of backend data, so the
 * same data is loaded once and a save updates every component showing it.
 *
 * @param props - `children` is the app.
 * @returns The provider wrapping the app.
 */
export function QueryProvider({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient);
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
