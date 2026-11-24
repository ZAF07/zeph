# Zeph UI — build contract

This folder is the design for the Zeph web app, in a form you build against and are tested against. The redesign is finished: every page in the app is built from these files. This file is now the contract for all UI work, including new pages and features. Read it fully before touching code.

Adding a page or a feature? Start with "Building new UI" below.

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
| `Memories` + six `Memories--tab-*` | `/memories`, `?tab=` | Seven tabs, one visible at a time: Memories, About you, What's going on, Patterns, What helps you, Day Summaries, Photos. `M-Memories--tab-patterns` is the Patterns tab on a phone. |
| `CheckIns`, `Account` | `/check-ins`, `/account` | |
| `Plan` | `/plan` | To build. UI only. |
| `Admin` | `/admin` | To build. Overview, replaces the redirect to Users. |
| `AdminUsers` | `/admin/users` | |
| `AdminCheckInLog` | `/admin/check-in-log` | Also the **table template**. |
| `AdminPersona`, `AdminPersonaOutlook` | `/admin/persona`, `?tab=outlook` | Voice and Outlook tabs. `AdminPersona` is also the **form template**. |
| `AdminPrompts` | `/admin/prompts` | Prompts & models. One folding card per core service, as in the card-list template, with "Model & settings" and "Prompts" groups inside. |
| `AdminModelCallTrace` | `/admin/model-calls/design-trace` | One trace from the Model call log. |
| `AdminEvalDaySummaryCase` | `/admin/evals/cases/day_summary/new` | The Day Summary Eval case form, and how a result reads. |
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

## Building new UI

Use this section for every new page, new feature, or visible change to an existing page.

### First, work out which kind of change it is

1. **A change to a page that has a reference file.** The reference still wins. If the change would look different from the reference (new copy, a new part, a new layout), the reference must change first. Ask Zaf to update `reference/<Ref>.html` and rebuild its baseline. Then build to match it. It is done when `compare.cjs` prints PASS for that page at both widths.
2. **A new admin page.** Build it from the template that fits: table (`AdminCheckInLog`), form (`AdminPersona`) or card list (`AdminCheckInKinds`). The foot of each template file lists the order its parts go in. Use the shared components below, with that page's real fields and columns. There is no pixel test for these pages, so in `/run` compare it by eye with the template at 1280 and 390.
3. **A new user page, or any page that needs a part no reference or template shows.** Stop and ask Zaf for a reference file first. Once it is in `reference/`, with its baseline and its line in `routes.json`, build it like any other page: done when `compare.cjs` passes at both widths.

You never edit `reference/`, `baseline/`, `tokens.css`, `routes.json`, `manifest.json` or the test scripts. Zaf changes the design; you build against it.

### Rules for all UI work

- Use only the values in `tokens.css` and the reference files: colours, sizes, weights, gaps, radii, shadows, icons, copy. No Tailwind default palette, no bold. If you need a value that is in neither, stop and ask.
- Reuse the shared components before writing new markup. A new component is fine when it only arranges existing parts and token values in a way a reference already shows.
- Build both widths, 1280 and 390. Layouts respond by wrapping, as in "Behaviour" above. Tables become cards on a phone. No sideways scrolling except the Memories tab row.
- Every part that loads or saves data uses the shared states from `States`: loading, empty, couldn't load, saved, save failed and confirm. See them in the app at `/design-preview/states` in fixture mode.
- A feature with no backend yet keeps the `ToBuildTag` and runs on fixture data only.
- If the page calls a new API client method, add its fixture data in `src/lib/design-fixtures/` so fixture mode keeps working.
- Check the page in the running app with real data (`/run`), not only fixtures: long names, many rows, nothing at all.
- Then run `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test`.

### Shared components

All in `src/components/`. Read a component's TSDoc before using it.

| Need | Components |
|---|---|
| Page frame | `DashboardShell` (every signed-in page), `PublicHeader`, `SiteFooter` |
| Page heading | `PageHero` (illustrated banner), `PageHeader` (plain), `AdminPageHeader`, `SectionIntro`, `Eyebrow` |
| Panels | `HomeCard`, `CardRow`, `PillLink` |
| Tables (table template) | `StatTiles`, `FilterPills`, `FilterPillLinks`, `SearchField`, `SelectFilter`, `DataTable`, `StatusPill`, `TableLoading`, `TableEmpty`, `TableNoMatches` |
| Forms (form template) | `FormSectionHeading`, `FormEditor`, `FieldRows`, `FieldRow`, `FieldText`, `FieldNumber`, `FieldSelect`, `Switch`, `SaveBar` |
| Card lists (card-list template) | `NewCardBox`, `CardList`, `CardListToolbar`, `FoldingCard`, `CardSaveBar`, `CardRemoveConfirm`, `CardListLoading` |
| Shared states | `LoadingPanel`, `LoadFailed`, `EmptyState`, `SavedNote`, `SaveFailedNote`, `ConfirmDialog` |
| Tags | `ToBuildTag`, `UnsavedTag` |

## Message-pipeline additions (20 Nov 2026)

The design changed for the issues in `.scratch/message-pipeline/issues`. Build each issue's UI against the files below. The test is the same: `node design/compare.cjs <Ref>` must print PASS.

| Issue | What changed in the design | Reference files |
|---|---|---|
| 05, 09 | Reply Plan is a core service with its own section. The woven-in Check-in prompt is gone. The trace shows Understanding and Reply Plan as separate steps, with the facts each one owns. | `AdminPrompts`, `AdminModelCallTrace` |
| 06 | Every editable field has a hint under its label: 13px, soft, at most two sentences. An editor gets a label and hint above it. | `AdminPrompts`, `AdminPersona`, `AdminCheckInKinds` |
| 07 | Persona has two tabs, Voice and Outlook, each with its own editor and save bar. The trace records "Read formed" and "Read said", and an Admin's own trace shows the Read in Content. | `AdminPersona`, `AdminPersonaOutlook`, `AdminModelCallTrace` |
| 08 | The user panel on Users lists "Confirmed Patterns". Pattern keeping is a core service with two limit rows. | `AdminUsers`, `AdminPrompts` |
| 10 | Memories has a Patterns tab: each confirmed Pattern, when the User agreed, what it is based on, and a delete button. | `Memories--tab-patterns`, `M-Memories--tab-patterns`, `States` (empty state) |
| 11, 12, 14 | New limits are ordinary field rows with hints. No new parts. | field rows in `AdminPersona` |
| 14 | The trace has a "Pattern" fact. | `AdminModelCallTrace` |
| 15 | Day Summary case form: Key, The day, Questions. A result shows the Summary written, then each question with Expected, the Judge's answer, Match or Miss, and the Judge's reason. | `AdminEvalDaySummaryCase` |
| 16 | "Conversation Summaries" is now "Day Summaries" everywhere: tab, heading, intro, hero line, and the delete texts. | every `Memories*` file, `Account`, `M-Account`, `States` |

**Copy.** The wording in these files is the wording to seed. For issue 10 the Copy slots are the Patterns heading, the line under it, the empty state title and body in `States`, and the delete button's label. For issue 16 take the tab name, heading, intro and delete texts from the reference files.

**Prompts & models.** `AdminPrompts` is the page as it is built today plus three additions: a hint under Model, Thinking and every limit; a Prompt label with its hint above each editor; and the two new services. Do not restyle anything else on a service card.

**Tabs.** The Persona tabs work like the Memories tabs: clicking swaps the editor and sets `?tab=outlook`. Unsaved text in one tab is kept when switching to the other.

**Fixtures.** Fixture mode must show exactly what is drawn. Prompts & models lists four services, in this order: Understanding, Reply Plan, Reply, Pattern keeping. The trace at `/admin/model-calls/design-trace` is the one drawn, an Admin's own, with all Content closed. The new Day Summary case form opens filled in as drawn. Alex has the two Patterns drawn. The annotation rows and the samples under them are rendered in fixture mode, as on the other template pages.

**Baselines.** After any change to `reference/`, Zaf runs `node design/shoot.cjs` on his own machine to rebuild `baseline/`. Baselines made on another machine render type differently and will not pass.

## Build order (the redesign, finished)

Kept as a record of how the redesign was built. New work follows "Building new UI" above.

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
