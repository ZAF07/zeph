import { QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderResult } from "@testing-library/react";
import type { ReactElement, ReactNode } from "react";

import { createQueryClient } from "@/lib/query-client";

/**
 * Renders a component for a test with its own empty cache of backend data,
 * so no test sees another's.
 *
 * @param ui - The component to render.
 * @returns What Testing Library's `render` returns.
 */
export function renderWithQueries(ui: ReactElement): RenderResult {
  const queryClient = createQueryClient();
  function wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
  }
  return render(ui, { wrapper });
}
