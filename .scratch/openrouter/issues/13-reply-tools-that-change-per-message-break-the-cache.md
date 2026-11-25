# 13 — Reply tools that change per message break the cache

Status: needs-triage

## Parent

`.scratch/openrouter/PRD.md` (user stories 19, 20). Found on 2026-11-25, in the code review of issue 09.

## What was found

A Claude model caches the tools and then the fixed part of the Reply's instructions (issue 09). Tools come first, so any change in a tool breaks the cache for that Reply, and it is written again.

Some tool descriptions are made for the message:

- `send_photo` lists the Shared Photos that matter for the message (`core/photos.py`).
- `ask_about_photo` lists the viewed photos in the Recent Messages (`core/photos.py`).
- `send_sticker` lists all stickers, so it changes only when one is added.

Two plain text messages in a row hit the cache (issue 09 `/run`). A turn where photos matter does not. Not measured yet how often that is.

## Acceptance criteria

- [ ] Measured: how often a Reply's tools differ from the Reply before it
- [ ] Decided: move the per-message lists out of the tool descriptions (e.g. into the per-message instructions), or leave as is
- [ ] If changed: `/run` shows a cache read on a second message where photos matter

## Comments
