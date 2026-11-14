# 08 — Dashboard: load and save data through TanStack Query

Status: completed

## Parent

Architecture review, 14 Nov 2026, point 7. Decided in a `/grill-with-docs` session.

## Why

About 20 client components copy the same load / save / error code. About 5 components fetch `/api/me` on each page (OnboardingGate, AdminGate, sidebar, the page itself); after one saves, the others show stale data. `UserMemorySetting.tsx` and `PhotoViewingSetting.tsx` are near copies.

## What to build

- Add TanStack Query (`@tanstack/react-query`) with one `QueryClientProvider`.
- Queries and mutations call the existing `@/lib/api-client` functions; pages still never call `fetch`.
- "me" is one query shared by every component; saves invalidate it so every component updates.
- Replace the copied load / save / error code; `useAdminSettings` moves onto it.
- One `PreferenceSwitch` component for User Memory and Photo Viewing.

## Decisions

- TanStack Query over our own hook + `MeProvider`: no rebuilding of caching, sharing and refresh; fewer backend calls at scale.
- Touches the lockfile (new dependency).

## Acceptance criteria

- [x] One `/api/me` request per page load, whatever the number of components using it
- [x] After a save, every component showing that data updates without a reload
- [x] Copied LoadState / saving / error code removed from components
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` pass
- [x] `/run` (run-dashboard): Home, Memories, Settings and admin pages load and save; network tab shows one `/api/me`

## Blocked by

None.

## Comments

### 14 Nov 2026 — plan (branch `arch-08-tanstack-query`)

- `lib/query-client.ts` (defaults: fresh for 30 s so components mounting together share one request; no retry, so errors show Try again at once), `lib/QueryProvider.tsx` in the root layout.
- `lib/queries.ts`: every cache key, plus named hooks for data shared across pages: `useMe`, `usePlatformContent`, `useUpdatePreferences`, `useCompleteOnboarding`, `useCheckIns`, `useSaveCheckIns`. One-off loads call `useQuery` / `useMutation` inline with `queryKeys.x`.
- `useAdminSettings` becomes a query; saving moves to `useSaveAdminSettings`.
- `PreferenceSwitch` replaces `UserMemorySetting` and `PhotoViewingSetting`.
- Tests render through `test/render-with-queries.tsx` (a fresh cache per test).

### 14 Nov 2026 — done

- Saves write the result into the cache (`setQueryData`) or invalidate what they change. Cross-page effects:
  - preferences → me + Home;
  - Check-in changes → Check-ins + me + Home (a Dashboard change clears "changed in chat");
  - onboarding → me + Check-ins + Home;
  - memory deletes → memory groups + Home;
  - Telegram connected → Home;
  - Delete my data → everything.
- `reloadUserPages()` (me, Home, platform content) is the one place for "an Admin change can reach the Admin's own pages". It is used by platform-settings saves, Feature switches and role changes.
- Rule used everywhere: show the data if there is any; show the error only when there is nothing to show. A failed background refresh never replaces a page with an error.
- Onboarding: the "already onboarded → go home" check runs only when the answers are first filled in. Otherwise saving would put an onboarded User in the cache and skip the Telegram step.
- Sign-out (`useSignOut`) clears the cache, so the next person on the tab never sees the last one's data.
- `useImageUrl` replaces three copies of the image loader (Shared Photo, Personal Sticker, Sticker Library pictures). It loads each image once per key.
- The managers' `runRowAction` (Helplines, Memory Categories, Knowledge) and the Knowledge document page's retry/delete now run on `useMutation`; `busyId` / `isBusy` and their try/catch are gone.
- Left as is on purpose:
  - `TelegramConnectionCard`'s polling state machine (ready → waiting → connected/expired). It is a flow, not the copied load code; it only gained the Home reload.
  - The eight child forms (`HelplineForm`, `MemoryCategoryForm`, `KnowledgeDetailsForm`, `KnowledgeTextSection`, `CheckInKindCard`, `StickerCard`, `KnowledgeReplaceFileForm`, `KnowledgeUploadForm`) keep `isSaving` / error around the `onSubmit` promise their manager passes in. They don't call the backend or read the cache.
  - The per-site "use the backend's refusal text, else a fallback" messages: status codes differ per site.
- Tradeoff: data counts as fresh for 30 s. A change made in chat (Telegram) can take up to 30 s to show on a page opened by link; window focus and every Dashboard save refresh at once.
- Code review (Standards and Spec in parallel):
  - Fixed: platform-settings saves didn't reload the User-facing text (AI notice, explanations, memory notes) — red test `use-admin-settings.test.tsx` first, then `reloadUserPages`; the "me/Home must reload" rule, copied in three components, moved into `reloadUserPages`; Memory Category changes now reload Home; row actions on `useMutation`; `useImageUrl` tests added.
  - Not changed: one-off queries stay inline rather than one hook per resource; `useSaveCheckIns` takes the call that sends the change, so one save status covers switch, frequency, quiet hours and pause; sign-out clearing the cache stays in `useSignOut`, the one place that knows a sign-out happened.
- Test-timing tweaks: two tests now wait for the call or the data, because TanStack runs mutations and resolves loads a tick later (`CheckInsSettings` quiet hours, `UserFeaturesPanel` first row).
- `/run` (worktree stack, ports 3140/8140/5572, signed in as an Admin Clerk test user, counting browser requests):
  - Full load of each page — Home, Memories, Check-ins, Account, and admin Users, Persona, Prompts, Safety, Features, Platform settings, Knowledge, Stickers, Memory Categories, Check-in Kinds, Check-in log, Safeguard Events, Usage — made exactly 1 `GET /api/me`, with no error blocks and no page errors.
  - Account: turned User Memory off, then opened Memories by the sidebar link. The header read "Memory paused" and the navigation made 0 `GET /api/me`. Turned it back on in Memories, opened Account by link: the switch was on.
  - Saved the name "Querytest" on Account, opened Home by link: the heading read "Good afternoon, Querytest." (then restored).
  - Admin Persona: saved an extra line, saw "Saved. Zeph uses it from the next message.", then restored it.
  - Platform settings: saved new Short AI notice wording; the sidebar showed it at once, without a reload (the review bug, after the fix). Then restored it.
  - Knowledge: uploaded a throwaway text document and opened its page (Ready). Delete returned to the Library; the document was gone from the list and from `knowledge_documents`.
  - Test users removed with `cleanup.sh`.

## Completion

- Completed: 2026-11-14
- Evidence per criterion:
  - One `/api/me` per page load: `OnboardingGate.test.tsx` "loads the User once for the gates, the sidebar and the page" (1 call); `queries.test.tsx` (3 components, 1 call); `/run` above (1 per page across 17 pages).
  - Every component updates after a save: `queries.test.tsx` "shows a saved change in every component without loading again"; `use-admin-settings.test.tsx`; `/run`: Account → Memories, name → Home, notice → sidebar, all without a reload.
  - Copied load/save/error code removed: `grep -rn "LoadState\|state\.kind ===\|type SaveState" web/src/components web/src/lib` finds none (outside tests). The only `useEffect` that calls `apiClient` is `TelegramConnectionCard` (kept, see Comments). `getMe()` is called only in `useMe`.
  - `pnpm lint` clean, `pnpm format:check` clean, `pnpm typecheck` clean, `pnpm test` 47 files / 330 tests passed.
  - `/run`: Home, Memories, Settings and admin pages load and save; one `/api/me` per page (see Comments).
- Commits:
  - 8fb67fd "Dashboard: load and save backend data through TanStack Query"
  - dbf24f7 "Review fixes: settings saves reload User pages, row actions on useMutation, useImageUrl tests"
  - c91faee "Knowledge document page: retry and delete on useMutation"
  - 39b2d75 "Architecture issue 08 done: archive issue with test, run and review evidence"
  - 9c98110 "ADR 0012: the Dashboard loads and saves backend data through TanStack Query"
  - b0a27e0 "Merge architecture issue 08: Dashboard loads and saves through TanStack Query" (merged from `arch-08-tanstack-query` into main)

