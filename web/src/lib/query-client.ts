import { QueryClient } from "@tanstack/react-query";

/**
 * Builds the cache that holds what the Dashboard has loaded from the
 * backend. Loaded data counts as fresh for 30 seconds, so components that
 * mount together share one request. A failed load is not retried: the page
 * shows its error with Try again straight away.
 *
 * @returns A new, empty cache.
 */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: false },
    },
  });
}
