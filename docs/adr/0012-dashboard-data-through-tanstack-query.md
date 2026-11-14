# The Dashboard loads and saves backend data through TanStack Query

Every Dashboard component loads and saves backend data through TanStack Query: one shared cache, queries and mutations that call the existing API client, and cache keys listed once in `web/src/lib/queries.ts`. We chose it over writing our own hook plus a `MeProvider`, because about 20 components were copying the same load / save / error code, and about 5 loaded `/api/me` on every page and showed stale data after another one saved. Our own version would have meant rebuilding caching, request sharing and refresh ourselves. With the library, each page makes one `/api/me` request, there are fewer backend calls at scale, and a save updates every component showing that data.

## Consequences

- A save either writes the result into the cache or invalidates the keys it changes. An Admin change that can reach the Admin's own pages (wording, a Feature, a role) calls `reloadUserPages()`.
- Loaded data counts as fresh for 30 seconds, so components that mount together share one request. A change made in chat can take up to 30 seconds to show on a page opened by a link. Going back to the window, or any Dashboard save, refreshes straight away.
- Signing out empties the cache.
- Forms that only show the progress of a promise their parent passes in keep their own small saving state. Only components that call the backend use queries and mutations.
