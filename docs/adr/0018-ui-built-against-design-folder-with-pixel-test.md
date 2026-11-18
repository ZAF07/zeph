# The Dashboard is built against `web/design/` and checked with a pixel test

`web/design/` is the only source of truth for how the Dashboard looks: `reference/*.html` holds every colour, size, gap, radius, line of copy and image position, `tokens.css` holds the theme, and `README.md` is the build contract. A page is done only when `web/design/compare.cjs` screenshots it in the running app, compares it with `baseline/<Ref>.png` and prints PASS at both widths (at most 0.5% of pixels differ, page height within 8px). We chose a pixel test over review by eye because agents building pages drift from a design in small ways (a gap, a weight, a colour from Tailwind's default palette) that no one notices one page at a time, and a diff image shows exactly where. It replaces the older `docs/design/` mockups.

For the test to mean anything the app must show the same data as the reference. So a design-fixture mode, on when `NEXT_PUBLIC_DESIGN_FIXTURES=1`, makes the API client return fixed data taken from the reference files, with a fixed clock. The signed-in person's name and role already come from the backend, so the fixture User is Alex, or the Admin Zaf when the browser carries a `zeph-design-as=admin` cookie; Clerk still handles the session itself. `?design=` query flags that force a state (menu folded, all steps, all folded) work only in this mode.

## Considered Options

- **Review by eye against the mockups.** Cheap, but it is how earlier pages drifted.
- **Component snapshot tests.** They check markup, not what the page looks like, so a wrong colour or gap still passes.
- **Pixel test against static reference pages (chosen).** Strict and needs fixture data, but it catches drift a person would miss.

## Consequences

- Nobody loosens `LIMIT`, adds a mask or edits a baseline to make a page pass. Baselines are rebuilt with `shoot.cjs` only when the design itself changes.
- Fixture mode lives only in the API client; pages don't know about it. It must never be reachable in a production build.
- Sign-in and sign-up mask the Clerk card and allow 8%, because the Clerk widget can't be matched pixel for pixel.
- Fixture data hides long names and many rows, so every page also gets a `/run` check with real data.
- Pages with no reference file are built from the admin templates (table, form, card list). Pages no template covers are restyled with the tokens and existing parts only, with no pixel test.
- `web/design/` is left out of lint and format checks, so its `.cjs` scripts stay plain JavaScript.
