# 20 — The pixel test hangs on Clerk's probe calls

Status: ready-for-human

## Parent

`.scratch/redesign/PRD.md` (found while closing `.scratch/pattern-pipeline/issues/archive/10-pattern-catalog-loads-and-admins-read-it.md`)

## Symptom

`node web/design/compare.cjs <Ref>` times out on every signed-in page, so the pixel test (ADR-0018) can't give a PASS or FAIL line as shipped.

Clerk's page script calls `*.client.protect.clerk.com:<odd port>/probe`. These calls never finish on this machine, inside and outside the sandbox. `compare.cjs` waits for the network to go quiet, which never comes.

Expected: the test loads each page and prints its PASS or FAIL line.

Impact: no UI work can be checked with the script as it is. Agents have been running a git-ignored copy with one added line, which the design README does not allow for the real script.

Seen on 24 Nov 2026 with Playwright 1.65.1.

## Repro

Deterministic on this machine.

1. `make up`
2. `eval "$(.claude/skills/run-dashboard/scripts/design-sessions.sh | grep '^export ')"`
3. `docker compose stop web`
4. `set -a; . ./.env; set +a`
5. `(cd web && NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev --port $WEB_PORT) &`
6. `BASE_URL=http://localhost:$WEB_PORT node web/design/compare.cjs AdminPatternCatalog`

The run times out at the page load.

Workaround that works: a copy of `compare.cjs` with this line added after the browser context is made:

```js
await ctx.route(/protect\.clerk\.com/, (route) => route.abort());
```

With it, `AdminPatternCatalog` prints `PASS AdminPatternCatalog 0.00% differs, height 2514 vs 2514`.

## Suspected location

`web/design/compare.cjs:41`: `await page.goto(BASE + r.path, { waitUntil: 'networkidle' });`

`web/design/README.md` says agents never edit the test scripts, so the fix is for the owner or Claude Design.

## Acceptance criteria

- [ ] `node web/design/compare.cjs <Ref>` finishes on signed-in pages with no local copy or patch
- [ ] A page that passed with the workaround still passes (e.g. `AdminPatternCatalog` at 0.00%)
- [ ] `.claude/skills/run-dashboard/SKILL.md` needs no extra step for this

## Comments
