# 08 — Dashboard: load and save data through TanStack Query

Status: ready-for-agent

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

- [ ] One `/api/me` request per page load, whatever the number of components using it
- [ ] After a save, every component showing that data updates without a reload
- [ ] Copied LoadState / saving / error code removed from components
- [ ] `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` pass
- [ ] `/run` (run-dashboard): Home, Memories, Settings and admin pages load and save; network tab shows one `/api/me`

## Blocked by

None.
