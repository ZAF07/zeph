"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import type {
  CheckIns,
  Me,
  ModelCallTraceFilter,
  OnboardingAnswers,
  PlatformContent,
  PreferenceChanges,
  SafeguardEventFilter,
} from "@/lib/api-client";
import { useApiClient } from "@/lib/use-api-client";

/** The cache key of each piece of backend data the Dashboard loads. */
export const queryKeys = {
  me: ["me"],
  platformContent: ["platform-content"],
  home: ["home"],
  memoryGroups: ["memory-groups"],
  conversationSummaries: ["conversation-summaries"],
  lifeThreads: ["life-threads"],
  userPortrait: ["user-portrait"],
  sharedPhotos: ["shared-photos"],
  checkIns: ["check-ins"],
  personalStickers: ["personal-stickers"],
  adminSettings: ["admin-settings"],
  coreServices: ["core-services"],
  adminUsers: ["admin-users"],
  features: ["features"],
  userFeatures: (userId: string) => ["user-features", userId],
  helplines: ["helplines"],
  safeguardEvents: (filter: SafeguardEventFilter) => [
    "safeguard-events",
    filter,
  ],
  checkInKinds: ["check-in-kinds"],
  needs: ["needs"],
  checkInLog: (days: number) => ["check-in-log", days],
  modelCallTraces: (filter: ModelCallTraceFilter) => [
    "model-call-traces",
    filter,
  ],
  modelCallTrace: (traceId: string) => ["model-call-trace", traceId],
  usage: (days: number) => ["usage", days],
  memoryCategories: ["memory-categories"],
  knowledgeDocuments: ["knowledge-documents"],
  knowledgeDocument: (documentId: string) => ["knowledge-document", documentId],
  stickers: ["stickers"],
  telegramConnection: ["telegram-connection"],
  sharedPhotoImage: (photoId: string) => ["shared-photo-image", photoId],
  personalStickerImage: (stickerId: string) => [
    "personal-sticker-image",
    stickerId,
  ],
  stickerImage: (stickerId: string) => ["sticker-image", stickerId],
} as const;

/**
 * Loads again what the signed-in User's own pages show: the User, Home and
 * the platform content. Admin changes that can reach the Admin's own pages
 * call this, such as a Feature switch, a role change or new wording.
 *
 * @param queryClient - The cache of backend data.
 */
export function reloadUserPages(queryClient: QueryClient): void {
  void queryClient.invalidateQueries({ queryKey: queryKeys.me });
  void queryClient.invalidateQueries({ queryKey: queryKeys.home });
  void queryClient.invalidateQueries({ queryKey: queryKeys.platformContent });
}

/**
 * The signed-in User, loaded once and shared by every component that shows
 * them.
 *
 * @returns The query for the User.
 */
export function useMe(): UseQueryResult<Me> {
  const apiClient = useApiClient();
  return useQuery({ queryKey: queryKeys.me, queryFn: () => apiClient.getMe() });
}

/**
 * The Admin-worded text the User pages show, such as the AI notice.
 *
 * @returns The query for the platform content.
 */
export function usePlatformContent(): UseQueryResult<PlatformContent> {
  const apiClient = useApiClient();
  return useQuery({
    queryKey: queryKeys.platformContent,
    queryFn: () => apiClient.getPlatformContent(),
  });
}

/**
 * Saves changes to the User's own settings. Every component showing the
 * User then shows the saved values, and Home loads again.
 *
 * @returns The mutation; pass it the changes.
 */
export function useUpdatePreferences(): UseMutationResult<
  Me,
  Error,
  PreferenceChanges
> {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (changes: PreferenceChanges) =>
      apiClient.updatePreferences(changes),
    onSuccess: (me) => {
      queryClient.setQueryData(queryKeys.me, me);
      void queryClient.invalidateQueries({ queryKey: queryKeys.home });
    },
  });
}

/**
 * Saves the User's onboarding answers. Every component showing the User
 * then sees them as onboarded, and their Check-ins and Home load again.
 *
 * @returns The mutation; pass it the answers.
 */
export function useCompleteOnboarding(): UseMutationResult<
  Me,
  Error,
  OnboardingAnswers
> {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (answers: OnboardingAnswers) =>
      apiClient.completeOnboarding(answers),
    onSuccess: (me) => {
      queryClient.setQueryData(queryKeys.me, me);
      void queryClient.invalidateQueries({ queryKey: queryKeys.checkIns });
      void queryClient.invalidateQueries({ queryKey: queryKeys.home });
    },
  });
}

/**
 * The User's Check-in settings and recent Check-ins.
 *
 * @returns The query for the Check-ins.
 */
export function useCheckIns(): UseQueryResult<CheckIns> {
  const apiClient = useApiClient();
  return useQuery({
    queryKey: queryKeys.checkIns,
    queryFn: () => apiClient.getCheckIns(),
  });
}

/**
 * Saves a change to the User's Check-ins: pass it the call that sends the
 * change. Every component then shows the saved Check-ins, and the User and
 * Home load again, since a change on the Dashboard clears "changed in chat".
 *
 * @returns The mutation; pass it the call that sends the change.
 */
export function useSaveCheckIns(): UseMutationResult<
  CheckIns,
  Error,
  () => Promise<CheckIns>
> {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sendChange: () => Promise<CheckIns>) => sendChange(),
    onSuccess: (checkIns) => {
      queryClient.setQueryData(queryKeys.checkIns, checkIns);
      void queryClient.invalidateQueries({ queryKey: queryKeys.me });
      void queryClient.invalidateQueries({ queryKey: queryKeys.home });
    },
  });
}
