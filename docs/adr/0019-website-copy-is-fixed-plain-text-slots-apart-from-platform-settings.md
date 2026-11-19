# Website Copy is fixed plain-text slots, kept apart from Platform Settings

Copy (the words Users and visitors read on the website) is Admin-managed like Platform Settings (ADR-0004), but it lives in its own store, seeded from its own file and edited on one Copy admin page. Platform Settings are what shapes the Companion: they reach the model, Eval Variants can override them, and they hold its chat wording. Copy never reaches the Companion, so mixing the two would put marketing text where Evals and replies look and blur who owns which words. Anything a User picks that the Companion is then told, such as the onboarding reason choices, stays a Platform Setting.

Each piece of Copy is a fixed slot that the code defines. Admins change the words only: no bold, links or HTML, and no adding, removing or moving slots. How the words look and where they sit come from the design, and the pages are held to it by the pixel test (ADR-0018), so this keeps an edit from breaking a page.

## Considered Options

- **Copy as more Platform Settings.** Rejected: it would mix website text with what shapes the Companion.
- **Markdown or rich text.** Rejected: styling belongs to the design, and links to routes belong in code. Bold lead-ins are split into their own slot instead.
- **Admins editing page structure** (adding sections, a page builder). Rejected for now: pages would drift from the design reference with no test to catch it. A list that really needs to grow becomes its own Admin-managed list.

## Consequences

- A save is turned away if a slot is over its max length or its placeholders (e.g. `{count}`) are missing or unknown. Plurals get a "one" and a "many" slot.
- One public endpoint, needing no sign-in, serves the Copy so signed-out visitors can see it. If the backend is down, the website shows its normal error state; no default text is bundled into the web app.
- Text from the backend's own rules (validation reasons) is not Copy.
- One language for now; adding languages later means adding text per slot, not reshaping it.
