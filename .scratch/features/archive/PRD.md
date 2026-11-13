# PRD: Features (Admin switches for everyone and for each User)

Status: completed

## Problem Statement

The owner plans paid plans after the MVP, where each plan includes only some of what the Companion offers. Today there is no single idea of "what the Companion offers". Web Search can be turned off for everyone, User Memory and Check-ins only by each User, and Stickers, Knowledge and Settings in Chat can't be turned off at all. An Admin can't turn anything off, or on, for one User: not to test something with one person, not to help a User having trouble, and not to prepare for plans. When plans arrive, this would have to be built from scratch, feature by feature.

## Solution

Every extra the Companion offers becomes a **Feature** with one on/off switch for everyone and one switch per User, both set by Admins. The Features in the MVP are Web Search, Check-ins, User Memory, Stickers, Knowledge and Settings in Chat; Photo Viewing joins when the photos PRD is built. A Feature works for a User only when the Admin side allows it and, where the User has their own switch (User Memory, Check-ins), the User has it on. A choice for one User (on or off) overrides the switch for everyone.

Admins get a clean **Features** page with every Feature's switch for everyone, and a **Features** panel per User on the Users page that shows each Feature's switch for that User, whether it works for them right now, and why. Each switch shows who changed it last and when.

A User whose Feature is turned off by an Admin sees "Not available on your account" on the Dashboard and can't switch it, and the Companion tells them plainly in chat that it isn't available on their account. Turning a Feature off never deletes anything. Safety and a User's rights and privacy are never Features: the Safeguard and Crisis Reply, the AI Notice, Delete My Data (in chat too) and seeing their own data on the Dashboard always work.

In the MVP every Feature is on for everyone. Later, a plan will be a set of Features, built on these switches rather than replacing them.

## User Stories

1. As an Admin, I want one page listing every Feature with its switch for everyone, so that I can see and change what the Companion offers in one place.
2. As an Admin, I want to turn a Feature off for everyone, so that I can stop it platform-wide (for cost, a bug or a policy reason).
3. As an Admin, I want to turn a Feature back on for everyone, so that it works again without a redeploy.
4. As an Admin, I want the Web Search switch on the Features page instead of the Settings page, so that every switch lives in one place.
5. As an Admin, I want to open a Features panel for any User from the Users page, so that I can manage what that User gets.
6. As an Admin, I want each Feature in that panel to be "default", "on" or "off" for that User, so that I can follow the setting for everyone, give one User a Feature that is off for everyone, or take one away.
7. As an Admin, I want "default" to follow the switch for everyone, so that most Users need no per-User setting at all.
8. As an Admin, I want the panel to show whether each Feature works for that User right now and why (e.g. "Off: turned off for everyone", "Off: the User turned it off", "On: turned on for this User"), so that I can answer "why can't they search the web?" without guessing.
9. As an Admin, I want to see who changed each switch last and when, so that I know whether another Admin made a change.
10. As an Admin, I want to turn a Feature on for one tester while it is off for everyone, so that I can try it with one person safely.
11. As an Admin, I want turning a Feature off to never delete a User's data, so that turning it back on (or a later plan upgrade) brings everything back.
12. As an Admin, I want Stickers to be a Feature, so that I can stop the Companion sending stickers for everyone or one User.
13. As an Admin, I want Knowledge to be a Feature, so that I can stop philosophy and mindfulness passages being added to replies for everyone or one User, ready for later plans with different Personas.
14. As an Admin, I want Settings in Chat to be a Feature, so that a lower plan can later require Users to change settings on the Dashboard.
15. As an Admin, I want User Memory and Check-ins to be Features, so that I can turn them off for a User even when that User has them on.
16. As an Admin, I want the Safeguard, Crisis Reply, AI Notice, Delete My Data and the User's own data on the Dashboard to never appear as Features, so that I can never switch off safety or a User's rights by mistake.
17. As an Admin, I want the Features page and panel to stay simple and easy to scan, so that managing switches is quick even with many Features.
18. As a User, I want a Feature an Admin turned off to show as "Not available on your account" on my Dashboard, so that I understand why I can't switch it.
19. As a User, I want my own choice (e.g. User Memory on) to be kept when an Admin turns that Feature off, so that it comes back the way I had it.
20. As a User, I want the Companion to tell me plainly when I ask for something that isn't available on my account, so that I'm not confused or misled.
21. As a User with Web Search off, I want the Companion to answer without looking things up, so that the chat still works.
22. As a User with Stickers off, I want replies without stickers, so that the chat still feels normal.
23. As a User with Knowledge off, I want replies without added passages, so that the chat still works.
24. As a User with User Memory off by an Admin, I want the Companion to neither keep nor use my memories, so that it behaves just like when I turn User Memory off myself.
25. As a User with User Memory off by an Admin, I want to still see and delete my existing memories on the Dashboard, so that my data stays in my control.
26. As a User with Check-ins off by an Admin, I want no Check-ins sent, so that the switch is respected.
27. As a User with Settings in Chat off, I want the Companion to point me to the Dashboard (with the link) when I ask to change a setting in chat, so that I know where to go.
28. As a User with Settings in Chat off, I want "delete my data" in chat to still work, so that my right to wipe my data never depends on a plan.
29. As a User in crisis, I want the Safeguard and Crisis Reply to work whatever Features I have, so that I always get help.
30. As a User, I want Delete My Data not to clear the Admin's switches for me, so that deleting my data can't be used to get around them (and nothing about my chats is in them).
31. As a User who deletes my account, I want my per-User switches deleted too, so that nothing about me is left behind.
32. As the owner, I want every Feature on for everyone in the MVP, so that testers get the full product.
33. As the owner, I want Features built so a plan can later just be a set of Features, so that adding paid plans extends this work instead of redoing it.

## Implementation Decisions

- **Feature list.** A fixed list in core: Web Search, Check-ins, User Memory, Stickers, Knowledge, Settings in Chat. The photos PRD adds Photo Viewing. Adding a Feature is a code change (it needs code that respects it); its switches are data.
- **Features core service** (new, ports-and-adapters like the rest of core). Its main question is "does this Feature work for this User?", which every other core service asks instead of reading switches itself. Interface, roughly:
  - `works_for(user, feature) -> bool`
  - `statuses_for(user) -> list of (feature, works, reason, admin switch for this User, last change)` for the Dashboard and the Admin panel
  - `set_for_everyone(feature, on, changed_by)` and `set_for_user(user, feature, default|on|off, changed_by)`
  - `list_for_everyone() -> list of (feature, on, last change)`
- **Rule.** Admin side = the per-User switch if it is "on" or "off", otherwise the switch for everyone. A Feature works when the Admin side is on and, for User Memory and Check-ins, the User's own switch is on too. Reasons are, in order: off for this User, off for everyone, the User turned it off.
- **Storage (migration).** One row per Feature for the switch for everyone (on/off, changed by, changed at), seeded all on. One row per User and Feature only when the per-User switch isn't "default" (on/off, changed by, changed at); setting it back to "default" removes the row. "Changed by" is the Admin's User; the UI shows their email.
- **Web Search switch moves.** The migration copies the current `web_search_enabled` platform setting into the Web Search switch for everyone and removes the setting, so it leaves the Settings page.
- **Where each Feature is respected:**
  - Web Search: the reply is offered the Web Search tools only when it works.
  - Stickers: the reply is offered the sticker tool only when it works. Incoming stickers are still read through their emoji.
  - Knowledge: Knowledge retrieval is skipped when it is off.
  - User Memory: memory retrieval, memory processing at Conversation end, and Check-in choice treat it exactly like the User's own User Memory off.
  - Check-ins: none are decided or sent when it is off; the Check-in Log is unchanged.
  - Settings in Chat: the settings tools aren't offered when it is off, except Delete My Data, which is always offered.
- **Telling the User in chat.** When any Feature doesn't work for a User, the reply instructions get a short Admin-managed note (new platform setting, ADR 0004) naming those Features and saying to tell the User plainly they aren't available on their account and, for settings, to change them on the Dashboard at `{dashboard_url}`.
- **Dashboard API.** The User endpoints that show User Memory and Check-in switches also return whether each Feature works and why. Changing a User's own switch for a Feature the Admin side has off is refused, and nothing is changed.
- **Admin API.** List and set the switches for everyone; list and set a User's per-User switches with statuses. Admin only, like the rest of the admin area.
- **Dashboard UI.** A new admin Features page (one row per Feature: name, short description, switch, last change). A Features button on each Users row opens a panel: one row per Feature with default/on/off, whether it works now and why, and last change. User pages show "Not available on your account" on switches the Admin side has off, and the switch is disabled. Keep both admin screens uncluttered.
- **Data.** Turning a Feature off deletes nothing. Delete My Data keeps the per-User switches (they are Admin settings, not the User's chat data). Account Deletion deletes them.
- **Never Features:** the Safeguard and Crisis Reply, the AI Notice, Delete My Data and the User seeing their own data. These never check a switch.

## Testing Decisions

- Good tests check what Users and Admins see and what the Companion does, through the public surfaces, not which tables or functions are used.
- **Seam 1 (backend HTTP, main).** Through the Telegram webhook and the Admin and Dashboard API, with the existing fakes and a real Postgres:
  - each Feature off (for everyone, and for one User) really stops working: no Web Search tool or sticker tool offered, no Knowledge passages, no memory used, settings tools not offered, with Delete My Data still working in chat;
  - per-User "on" overrides "off for everyone"; per-User "default" follows it;
  - the User's own switch is kept and still applies when the Admin side turns back on;
  - statuses and reasons, and last change (who, when);
  - the reply instructions include the "not available on your account" note only when a Feature is off;
  - a User can't switch on a Feature the Admin side has off;
  - Web Search's old setting is carried over by the migration;
  - Delete My Data keeps per-User switches, Account Deletion removes them; non-Admins can't call the admin endpoints.
  - Prior art: the web search, stickers, settings-via-chat, user memory API and admin settings tests.
- **Seam 2 (scheduler tick).** Check-ins aren't sent and memory processing keeps nothing when the Admin side has the Feature off. Prior art: the Check-in sending and post-conversation tests.
- **Seam 3 (Dashboard).** The admin Features page, the per-User panel, and "Not available on your account" on User pages, with the API client mocked. Prior art: the admin Users and platform settings form tests.

## Out of Scope

- Paid plans, billing and payment, and any "Upgrade" button. The "Not available on your account" text is where "Upgrade" will go later.
- Choosing between several Personas (after the MVP, by plan).
- Photo Viewing itself, which is added to the Feature list by the photos PRD.
- A full history of switch changes; only the last change is kept.
- Making limits (Daily Message Limit, Web Search Limit) part of plans; they stay numbers for now.

## Further Notes

- Decisions come from the 2026-11-13 grilling session, logged in the archived issue `.scratch/mvp/issues/archive/19-companion-pretends-to-see-photos.md`. Glossary: **Feature** in `CONTEXT.md`. Related ADRs: 0004 (settings are Admin-managed data), 0006 (settings in chat; Settings in Chat now becomes a Feature).
- Build this before the photos PRD, which depends on the Features core service.

## Completion

- Completed: 2026-11-14
- Delivered by issues 01–05 (all archived in `.scratch/features/issues/archive/`); Photo Viewing joined the Feature list in photos issue 07:
  - 01 Features core service and Web Search switch: fb78a73, review fixes d22e509, archive 50d2560
  - 02 Per-User Feature switches: 50fdada, review fixes 0161961, archive 3f48771
  - 03 Stickers and Knowledge Features: 41766d3, review fixes 88ffc67, archive 85900de
  - 04 User Memory and Check-ins Features: b7af9cb, review fixes 34e690a, archive 57014ae
  - 05 Settings in Chat Feature: 1b8a9e2, review fixes f0833d6, archive 166f2b1
- Checks on close-out (main at 1e9d936): ruff, ruff format, mypy pass; pytest 597 passed; pnpm lint, format:check, typecheck pass; Vitest 321 passed
- Commit: <to be filled in manually>
