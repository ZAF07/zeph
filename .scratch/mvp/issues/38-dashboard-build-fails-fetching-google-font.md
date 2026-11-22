# 38 — Dashboard build fails when the Google font can't be fetched

Status: needs-triage

## Parent

`.scratch/mvp/PRD.md`

## Symptom

On the production VPS, `make restart` failed while building the Dashboard image. The build stopped at `RUN pnpm build` (`web/Dockerfile:16`) with:

```
> Build failed because of webpack errors
[ELIFECYCLE] Command failed with exit code 1.
target web: failed to solve: process "/bin/sh -c pnpm build" did not complete successfully: exit code: 1
make: *** [Makefile:43: restart] Error 1
```

The webpack error was in `next/font/google` loading the **Outfit** font for `src/app/layout.tsx`. Next.js downloads Google fonts while building, so a build that can't reach Google Fonts fails as a whole. Expected: the Dashboard builds without needing the internet for fonts.

Impact: no deploy can go out while it happens. Issue 31's deploy-on-push runs the same build on the server. The running containers stay up, because a failed build doesn't replace them.

Reported 2026-11-22 by the owner, from the VPS. Only the last lines of the output were captured; the error line above them (probably `Failed to fetch font 'Outfit'`) was not.

## Repro

On the VPS, as `deploy`, in `~/zeph`: `make restart`. It's not known yet whether it fails every time or only now and then. The same build works on the owner's Mac.

To see whether containers on the server can reach Google Fonts:

```
docker run --rm node:22-alpine wget -qO- -T 10 "https://fonts.googleapis.com/css2?family=Outfit" | head -3
```

## Suspected location

`web/src/app/layout.tsx:2`: `import { Outfit } from "next/font/google";`

## Acceptance criteria

- [ ] The Dashboard image builds with no network access to Google Fonts
- [ ] A test or check covers it, so a build-time font download can't come back unnoticed
- [ ] The Dashboard still looks the same (pixel test, `web/design/compare.cjs`)
- [ ] The repo's checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] `make restart` on the VPS builds and the live Dashboard loads

## Blocked by

None
