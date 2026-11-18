# Zeph redesign — build contract

This folder is the design for the Zeph web app, in a form you build against and are tested against. It replaces the current light theme. Read this file fully before touching code.

## The one rule

`reference/*.html` is the design. It is not inspiration. Every colour, size, gap, radius, line of copy and image position in the app must be the one in the reference file for that page. Where the reference and your instinct differ, the reference wins. Where the reference and this file differ, stop and ask.

You do not get to: add or change colours, font sizes, weights, spacing, radii, shadows, icons, animations or copy; "tidy" a layout; swap a component for a library one; use Tailwind's default palette; use bold. If something seems wrong or missing in the design, say so and wait. Do not fill the gap yourself.

A page is finished when `node design/compare.cjs <Ref>` prints PASS for it at both widths, and not before. Never loosen `LIMIT`, add a mask, or edit a baseline to make a page pass.

## What is in here

| Path | What it is |
|---|---|
| `reference/<Ref>.html` | One plain HTML file per page and state. Inline styles hold the exact values. Open them in a browser. `M-` files are the 390px phone layouts. |
| `reference/img/*.jpg` | The seven illustrations, named by where they go. |
| `reference/fonts/` | Outfit, used only so the reference renders offline. The app loads Outfit with `next/font/google`. |
| `baseline/<Ref>.png` | Full-page screenshots of the reference files. These are what the app is compared with. |
| `tokens.css` | The Tailwind 4 `@theme` block and the type and spacing scale. |
| `routes.json` | Which app route, width and sign-in state each reference file corresponds to. |
| `compare.cjs` | The acceptance test: screenshots the app and diffs it against `baseline/`. |
| `shoot.cjs`, `manifest.json` | Regenerates `baseline/` from `reference/`. Only the designer runs this. |
| `PROMPTS.md` | The prompts Zaf pastes to start each slice. |

## How to read a reference file

The files are static: no script, sample data baked in. Sample people, dates and counts ("Alex", "12 Nov", "212") are fixtures, described below. Text in `[SQUARE BRACKETS]` is a placeholder that stays a placeholder: render it literally. An orange "TO BUILD" tag marks a feature with no backend yet: build the UI exactly as drawn, wired to fixture data only, and keep the tag. Orange dashed rows such as "OTHER STATES OF THIS TABLE" are annotations for you: they and the samples under them are not part of the page, but each sample is the exact design for that state.

Translate inline styles to Tailwind classes using the tokens, with arbitrary values (`gap-[22px]`) where no token exists. The computed result must equal the inline style. Keep the flex-basis and wrap values exactly: the layouts respond by wrapping, not by breakpoints, and the phone files show the result. The only breakpoint-style switches are the ones listed under "Behaviour".

## Pages and routes

| Reference | Route | Notes |
|---|---|---|
| `Landing` | `/` signed out | New page. Signed-in users at `/` still get Home. |
| `HowItWorks` | `/how-it-works` | New page, public. |
| `Login`, `Signup` | `/sign-in`, `/sign-up` | Rework `AuthLayout`. The card is a stand-in for the Clerk widget: style Clerk with its `appearance` prop to match the card's colours, radii, type and button, and put `data-clerk-card` on its wrapper. Layout, image, header and legal lines must match exactly. |
| `Onboarding` | `/onboarding` | The file stacks all six steps, separated by dashed lines, so each is visible. The app shows one at a time, as now. `?design=all-steps` renders them stacked for the test. |
| `ConnectTelegram` | `/connect-telegram` | Main card plus its other states. |
| `Dashboard` | `/` signed in | Home. |
| `Memories` + five `Memories--tab-*` | `/memories`, `?tab=` | Six tabs, one visible at a time. |
| `CheckIns`, `Account` | `/check-ins`, `/account` | |
| `Plan` | `/plan` | To build. UI only. |
| `Admin` | `/admin` | To build. Overview, replaces the redirect to Users. |
| `AdminUsers` | `/admin/users` | |
| `AdminCheckInLog` | `/admin/check-in-log` | Also the **table template**. |
| `AdminPersona` | `/admin/persona` | Also the **form template**. |
| `AdminCheckInKinds` | `/admin/check-in-kinds` | Also the **card-list template**. |
| `States` | none | Sheet of empty, loading, error, saved and confirm parts used by every page. |

Admin pages with no reference file of their own are built from a template, and the template file names which pages it covers at its foot. Use the template's parts in the template's order, with that page's real fields and columns. If a page needs a part no template has, stop and ask.

## Behaviour the static files cannot show

**Sidebar (1280).** Sticky: it stays in view while the page scrolls (`position: sticky; top: 0; height: 100vh`, own scroll if taller). The fold button swaps it for the 76px icon rail in `Dashboard--menu-folded`. Remember the choice in `localStorage`. `?design=menu-folded` forces it for the test.

**Phone menu (390).** Below 900px the sidebar is replaced by the sticky top bar in `M-Dashboard`. The menu button opens the panel in `M-Menu`, pushing content down, and the icon becomes a cross. Choosing a link closes it. `?design=menu-open` forces it open.

**Public header (390).** Nav links collapse behind the menu button, as in `M-Landing--nav-open`.

**Memories tabs.** Clicking a tab swaps the panel below without navigating away, and sets `?tab=`. Selected tab: cream text, weight 400, 2px cream underline. On a phone the tab row scrolls sideways and never wraps.

**Card lists.** The whole top row of a card toggles it. The chevron points right when folded and down when open. Several can be open at once. "Expand all" and "Collapse all" do what they say. A card with unsaved edits shows the orange "Unsaved changes" tag on its folded row and keeps its text when folded. `?design=all-folded` renders every card folded.

**Check-in frequency.** One row of four equal segments on desktop, two rows of two on a phone. The selected one is the cream pill.

**Tables on a phone.** Each row becomes a card of label and value lines, as in `M-AdminCheckInLog`. No sideways-scrolling tables.

**Connect Telegram on a phone.** No QR code. The button is the action.

**Motion.** None beyond the browser default, except a 150ms ease on the chevron rotation and on hover colour. Respect `prefers-reduced-motion`.

**Focus.** A 2px cream outline with 2px offset on every focusable element. Keep every `aria-` attribute and label in the reference.

## Images

Seven illustrations, served from `public/design/` under the same file names as `reference/img/`. Zaf supplies full-resolution versions with the same names and the same 16:9 framing. Never crop, recolour, compress below quality 85, or replace one.

Use them as CSS backgrounds with the declarations below, copied exactly, including every gradient layer. Do not use `next/image` for these: the placement depends on `background-position` and `background-size`. Only the `url()` path changes.

### `Landing.html` · `.zh` · `hero-pavilion.jpg`

```css
background: linear-gradient(180deg,rgba(10,32,44,0) 80%,#0A202C 100%),linear-gradient(90deg,rgba(10,32,44,.55) 0%,rgba(10,32,44,0) 55%),url(img/hero-pavilion.jpg) right bottom/cover no-repeat #0A202C;
```

### `M-Landing.html` · `.zh` · `hero-pavilion.jpg`

```css
background: linear-gradient(180deg,rgba(10,32,44,0) 86%,#0A202C 100%),linear-gradient(180deg,#0A202C 0%,#0A202C calc(100% - 430px),rgba(10,32,44,0) calc(100% - 300px)),url(img/hero-pavilion.jpg) right bottom/auto 430px no-repeat #0A202C;
```

### `Landing.html` · `.zf` · `faq-doorway.jpg`

```css
background: linear-gradient(180deg,#0A202C 0%,rgba(10,32,44,0) 30%,rgba(7,25,34,0) 92%,#071922 100%),url(img/faq-doorway.jpg) left bottom/cover no-repeat #0A202C;
```

### `M-Landing.html` · `.zf` · `faq-doorway.jpg`

```css
background: linear-gradient(180deg,#0A202C 0%,#0A202C calc(100% - 390px),rgba(10,32,44,0) calc(100% - 260px),rgba(7,25,34,0) 92%,#071922 100%),url(img/faq-doorway.jpg) left bottom/auto 390px no-repeat #0A202C;
```

### `HowItWorks.html` · `.zw` · `how-stepping-stones.jpg`

```css
background: linear-gradient(180deg,rgba(10,32,44,0) 72%,#0A202C 100%),linear-gradient(90deg,rgba(10,32,44,.72) 0%,rgba(10,32,44,0) 58%),url(img/how-stepping-stones.jpg) right 62%/cover no-repeat #0A202C;
```

### `M-HowItWorks.html` · `.zw` · `how-stepping-stones.jpg`

```css
background: linear-gradient(180deg,rgba(10,32,44,0) 88%,#0A202C 100%),linear-gradient(180deg,#0A202C 0%,#0A202C calc(100% - 410px),rgba(10,32,44,0) calc(100% - 290px)),url(img/how-stepping-stones.jpg) right bottom/auto 410px no-repeat #0A202C;
```

### `Login.html` · `.zl` · `auth-archway.jpg`

```css
background: linear-gradient(180deg,rgba(10,32,44,.25),rgba(10,32,44,.25)),url(img/auth-archway.jpg) left bottom/cover no-repeat #0A202C;
```

### `M-Login.html` · `.zl` · `auth-archway.jpg`

```css
background: linear-gradient(180deg,#0A202C 0%,#0A202C calc(100% - 390px),rgba(10,32,44,0) calc(100% - 260px)),url(img/auth-archway.jpg) left bottom/auto 390px no-repeat #0A202C;
```

### `Dashboard.html` · `.zb` · `home-bench.jpg`

```css
background: linear-gradient(90deg,rgba(10,32,44,.82) 0%,rgba(10,32,44,.55) 42%,rgba(10,32,44,0) 68%),url(img/home-bench.jpg) right 64%/cover no-repeat #0A202C;
```

### `M-Dashboard.html` · `.zb` · `home-bench.jpg`

```css
background: linear-gradient(180deg,#0A202C 0%,#0A202C 24%,rgba(10,32,44,.6) 42%,rgba(10,32,44,0) 58%),url(img/home-bench.jpg) right bottom/auto 78% no-repeat #0A202C;
```

### `Memories.html` · `.zm` · `memories-niches.jpg`

```css
background: linear-gradient(90deg,rgba(10,32,44,.82) 0%,rgba(10,32,44,.55) 42%,rgba(10,32,44,0) 68%),url(img/memories-niches.jpg) right 64%/cover no-repeat #0A202C;
```

### `M-Memories.html` · `.zm` · `memories-niches.jpg`

```css
background: linear-gradient(180deg,#0A202C 0%,#0A202C 24%,rgba(10,32,44,.6) 42%,rgba(10,32,44,0) 58%),url(img/memories-niches.jpg) right bottom/auto 78% no-repeat #0A202C;
```

### `CheckIns.html` · `.zc` · `checkins-beacon.jpg`

```css
background: linear-gradient(90deg,rgba(10,32,44,.82) 0%,rgba(10,32,44,.55) 42%,rgba(10,32,44,0) 68%),url(img/checkins-beacon.jpg) right 64%/cover no-repeat #0A202C;
```

### `M-CheckIns.html` · `.zc` · `checkins-beacon.jpg`

```css
background: linear-gradient(180deg,#0A202C 0%,#0A202C 24%,rgba(10,32,44,.6) 42%,rgba(10,32,44,0) 58%),url(img/checkins-beacon.jpg) right bottom/auto 78% no-repeat #0A202C;
```

## Fixtures, so the test means something

The comparison only works if the app shows the same data as the reference. Add a design-fixture mode, on when `NEXT_PUBLIC_DESIGN_FIXTURES=1`, in which the API client returns fixed data instead of calling the backend. Take every value from the reference files: the user is Alex (`alex@example.com`), the admin is Zaf, and the memories, check-ins, users, log rows and counts are the ones drawn. Fix the clock so the greeting reads "Good evening". Fixture mode must never be reachable in a production build.

The `?design=` query flags listed above are honoured only in fixture mode.

For signed-in pages the test needs two Playwright `storageState` files, a user and an admin, passed as `STATE_USER` and `STATE_ADMIN`. Ask Zaf how he wants these created. Do not put credentials in the repo.

## Running the test

```
pnpm add -D playwright pixelmatch pngjs
NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev
node design/compare.cjs                # everything
node design/compare.cjs Dashboard M-Dashboard
```

PASS means at most 0.5% of pixels differ and the page height is within 8px. On FAIL, open `design/.diff/<Ref>.png`: red marks every pixel that differs. Fix the app, not the test. Add `design/.diff/` to `.gitignore`.

The sign-in and sign-up pages mask the Clerk card on both sides and allow 8%, because the Clerk widget cannot be matched pixel for pixel. Everything around the card is still checked.

## Build order

One slice at a time. After each: run the test for that slice's pages, run `pnpm lint`, `pnpm typecheck` and `pnpm test`, report the PASS lines, list anything you were unsure about, then stop and wait for Zaf.

0. **Foundations.** Replace the `@theme` block with `tokens.css`, load Outfit, copy images to `public/design/`, add fixture mode, wire `compare.cjs`, and add `design/` to `.prettierignore` and the ESLint ignores so the lint and format checks skip this folder. Existing pages will look broken after this. That is expected.
1. **Shell.** Sidebar, fold, rail, phone bar and menu. Test with `Dashboard--menu-folded`, `M-Menu`.
2. **Home.** `Dashboard`, `M-Dashboard`.
3. **Memories.** All six tabs, `M-Memories`.
4. **Check-ins.** `CheckIns`, `M-CheckIns`.
5. **Account & privacy.** `Account`, `M-Account`.
6. **Connect Telegram.** `ConnectTelegram`, `M-ConnectTelegram`, plus its other states.
7. **Onboarding.** `Onboarding`, `M-Onboarding`.
8. **Sign in and sign up.** `Login`, `Signup`, `M-Login`.
9. **Public pages.** `Landing`, `HowItWorks`, their phone files, and the `/` routing.
10. **Shared states.** Every empty, loading, error, saved and confirm state in `States`, applied across the pages above.
11. **Admin shell and Users.** `AdminUsers`.
12. **Table pages.** `AdminCheckInLog` first, then the pages its foot lists.
13. **Form pages.** `AdminPersona` first, then the pages its foot lists.
14. **Card-list pages.** `AdminCheckInKinds` first, then the pages its foot lists.
15. **To build.** `Plan` and `Admin` overview, UI on fixtures only. No billing code.

Existing behaviour, API calls, tests and Clerk logic stay as they are. This is a reskin and re-layout, plus the new pages named above. Update existing component tests only where markup they assert on has changed, and say which.

## When to stop and ask

Stop if: a reference file and existing behaviour conflict; a page needs a part no reference shows; real data would not fit the drawn layout (long names, many rows); a PASS seems impossible without changing the test; or you are about to choose a value that is not in a reference file.
