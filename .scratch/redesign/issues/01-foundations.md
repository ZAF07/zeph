# 01 — Redesign: foundations (images, tokens, font, fixture mode, pixel test, sessions)

Status: ready-for-agent

Lane: solo. Runs before any other redesign issue. README slice: 0.

## Parent

`.scratch/redesign/PRD.md`

## What to build

Set up everything the other issues build on. Do it in this order:

1. **Full-resolution images.** Zaf has put PNGs in `web/design/img-full/`, named to match the seven JPGs in `web/design/reference/img/`. Convert each one to a JPG of the same name at quality 90, keeping the size and framing (macOS: `sips -s format jpeg -s formatOptions 90 <in>.png --out <out>.jpg`). Replace the files in `reference/img/`, then delete `img-full/`. If any file is missing, misnamed or not 16:9, stop and ask.
2. **Rebuild the baselines once** with `shoot.cjs`, from the new images. This is the only baseline change allowed in the whole redesign.
3. **Theme and font.** Replace the `@theme` block with `web/design/tokens.css`. Load Outfit with `next/font/google` (weights 300, 400, 500, 600) as `--font-outfit`. Copy the images to the app's public `design/` folder.
4. **Design-fixture mode** (ADR 0018). It's on only when `NEXT_PUBLIC_DESIGN_FIXTURES=1`, read through the typed `env` module, and never reachable in a production build. The API client factory returns a fixture client with the same interface. Pages don't know about it. `/api/me` returns Alex (`alex@example.com`) as a User, or Zaf as an Admin when the browser has the `zeph-design-as=admin` cookie. The clock is fixed so the greeting reads "Good evening". `?design=` flags are read only in fixture mode. Set up **one fixture file per page area** (home, memories, check-ins, account, telegram, onboarding, admin-users, admin-tables, admin-forms, admin-cards, plan, overview), so later issues running in parallel each fill their own. This issue fills only what `/api/me` and the shell need.
5. **Pixel test wiring.** Add `playwright`, `pixelmatch` and `pngjs` as dev dependencies. Add `design/.diff/` to `.gitignore`. Leave `design/` out of ESLint and Prettier (its `.cjs` scripts stay plain JavaScript).
6. **Sign-in sessions for the test.** Add a script that makes `STATE_USER` and `STATE_ADMIN` Playwright storageState files by reusing the run-dashboard skill's `start-session.sh` (User, and Admin with the `zeph-design-as=admin` cookie added). It writes them outside the repo and prints the paths. Add a matching clean-up that deletes the Clerk test users. No credentials go in the repo.
7. **One source of truth.** Delete `docs/design/`. Change the "UI design" section of `CLAUDE.md` to point to `web/design/README.md` (and ADR 0018).

Existing pages will look broken after this. That's expected, and so is merging it to main.

Refs: none pass yet. This issue proves the test runs.

## Acceptance criteria

- [ ] Seven JPGs in `reference/img/` come from the full-resolution PNGs at quality 90, `img-full/` is gone, and the baselines are rebuilt once with `shoot.cjs` (diff stat pasted).
- [ ] The theme is exactly `tokens.css`, and no Tailwind default colour classes resolve.
- [ ] Outfit loads through `next/font/google`.
- [ ] With the flag on, `/api/me` returns Alex, or Zaf with the admin cookie. With the flag off, the real client is used. Covered by a test.
- [ ] A production build doesn't contain the fixture client (checked and shown).
- [ ] The session script makes both files outside the repo, and the clean-up removes the test users.
- [ ] `node design/compare.cjs Dashboard` runs end to end and writes a diff image. FAIL is expected here.
- [ ] `docs/design/` is deleted and `CLAUDE.md` points at `web/design/README.md`.
- [ ] Before coding, the agent replied to the once-at-start prompt in `web/design/PROMPTS.md` and Zaf answered its questions.

## Blocked by

None. It can start immediately, once Zaf has put the PNGs in `web/design/img-full/`.

## Rules for every redesign issue

- Read `web/design/README.md` in full, then every reference file named here at both widths, before coding. The README wins on look, copy and behaviour. Where it and this issue differ, stop and ask. Its "When to stop and ask" list applies.
- Build so the computed styles equal the reference's inline styles. Take copy, sizes, colours, gaps and image CSS from the reference, never from memory. Use only the tokens (arbitrary values like `gap-[22px]` where no token exists).
- Never change anything in `web/design/` (`LIMIT`, masks, baselines, references), except the one image swap and baseline rebuild in issue 01.
- Own worktree (`make worktree-setup`), own branch, own PR. Run the pixel test with `BASE_URL=http://localhost:$WEB_PORT`, `NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev`, and the two session files from issue 01's script.
- **Parallel work.** Two agents work at once. Put this issue's sample data in its own fixture file for its page area, and don't edit another area's file. Only issue 01 edits the theme, font, fixture switch and pixel-test setup. Only issue 02 edits the sidebar and menu. Only issue 08 edits the middleware. If you need a change in one of those, stop and ask.
- Use the shared state parts from issue 03 (empty, loading, error, saved, confirm) for every state this issue's pages show (from issue 04 on).
- Existing behaviour, API calls, Clerk logic and tests stay as they are. Update a test only where the markup it checks has changed.
- Before the PR: `git fetch origin && git rebase origin/main`, then re-run this issue's pixel test and checks.

## Done when (for every redesign issue)

- [ ] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs.
- [ ] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [ ] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [ ] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [ ] `/code-review` run, and findings fixed or answered.

## Comments
