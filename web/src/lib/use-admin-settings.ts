"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import type { AdminSettings, SettingValue } from "@/lib/api-client";
import { queryKeys } from "@/lib/queries";
import { useApiClient } from "@/lib/use-api-client";

/**
 * The platform settings Admins edit, loaded once and shared by every admin
 * page, so each page only decides which settings it shows.
 *
 * @returns The query for the settings.
 */
export function useAdminSettings(): UseQueryResult<AdminSettings> {
  const apiClient = useApiClient();
  return useQuery({
    queryKey: queryKeys.adminSettings,
    queryFn: () => apiClient.getAdminSettings(),
  });
}

/**
 * Saves new values for platform settings. Every admin page then shows the
 * saved settings. It fails with the backend's `ApiError` if the backend
 * refuses them.
 *
 * @returns The mutation; pass it the new values by setting key.
 */
export function useSaveAdminSettings(): UseMutationResult<
  AdminSettings,
  Error,
  Record<string, SettingValue>
> {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (values: Record<string, SettingValue>) =>
      apiClient.updateAdminSettings(values),
    onSuccess: (settings) =>
      queryClient.setQueryData(queryKeys.adminSettings, settings),
  });
}
