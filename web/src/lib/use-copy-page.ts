"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import type { CopyTab } from "@/lib/api-client";
import type { Copy } from "@/lib/copy";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/** One tab's save: the tab's key and the new text for each changed slot. */
export type CopyTabSave = { tab: string; texts: Copy };

/**
 * The Copy page Admins edit: every tab with its slots in page order.
 *
 * @returns The query for the Copy page.
 */
export function useCopyPage(): UseQueryResult<CopyTab[]> {
  const apiClient = useApiClient();
  return useQuery({
    queryKey: queryKeys.copyPage,
    queryFn: () => apiClient.getCopyPage(),
  });
}

/**
 * Saves one tab's changed texts, all together or not at all. The page then
 * shows the saved Copy. It fails with the backend's `ApiError`, with a
 * reason per slot in `fields`, if any text is turned away.
 *
 * @returns The mutation; pass it the tab and its changed texts.
 */
export function useSaveCopyTab(): UseMutationResult<
  CopyTab[],
  Error,
  CopyTabSave
> {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ tab, texts }: CopyTabSave) =>
      apiClient.saveCopyTab(tab, texts),
    onSuccess: (tabs) => {
      queryClient.setQueryData(queryKeys.copyPage, tabs);
    },
  });
}
