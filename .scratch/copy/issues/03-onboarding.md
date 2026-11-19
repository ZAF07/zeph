# 03 — Copy: Onboarding, and the words around sign-in and sign-up

Status: ready-for-agent

Lane: A.

## Parent

`.scratch/copy/PRD.md`

## What to build

Onboarding reads every word from Copy (headings, questions such as "What brings you here?", field labels, buttons, its own error messages, tab title and description), with an Onboarding tab on the Copy page. Our words around the Clerk sign-in and sign-up forms are Copy too; the text inside Clerk's forms is not.

Not part of this issue:
- The onboarding reason choices stay a Platform Setting (the Companion is told them).
- The AI notice text shown during onboarding stays where it is until issue 08 moves it.

## Acceptance criteria

- [ ] Onboarding and the sign-in/sign-up surrounds show only Copy text; no default text in web code.
- [ ] The reason choices still come from Platform Settings and still save on the User.
- [ ] The Copy page shows an Onboarding tab (and the sign-in/sign-up slots in their tab), slots in page order.
- [ ] Seed text matches the references; the pixel test passes for these pages at both widths.
- [ ] Tests cover the converted pages; all Python and web checks pass.
- [ ] `/run`: as an Admin, edit an onboarding question, then go through onboarding as a new User and see it.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`
