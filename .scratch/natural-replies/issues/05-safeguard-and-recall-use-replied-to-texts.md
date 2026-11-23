# 05 — The Safeguard and Recall use Replied-to Texts

Status: ready-for-agent
Track: B
Blocked by: 04

## Parent

`.scratch/natural-replies/PRD.md`

## What to build

- **Safeguard:** reads each text with its Replied-to Text as it arrives, in the same call. A "yes" sent as a reply to Zeph asking about self-harm must be read with that question. It is still checked as the text arrives, never held back by the wait.
- **Recall:** the search text for Life Threads, Patterns and Move Outcomes adds the Replied-to Texts of the Message's texts to what the Understanding says the User means and the latest texts. A reply to a weeks-old text brings back the Thread it was about.

## Acceptance criteria

- [ ] The Safeguard's prompt for a text includes its Replied-to Text.
- [ ] "yes" as a reply to Zeph's self-harm question gets the Crisis Reply (fake model set to flag it; the test checks the question reached the Safeguard).
- [ ] Recall's search includes the Replied-to Text, and a Thread close only to the replied-to text comes to mind.
- [ ] A text with no Replied-to Text is checked and searched as today.
- [ ] Tests through the webhook (fake chat model prompts, fake embeddings); all Python checks pass.
- [ ] `/run`: in a worktree, reply to an old Zeph text about a known Thread and see that Thread among those reminded in the trace.
- [ ] `docs/message-pipeline/README.md` decision 20 note updated to "Built".

## Blocked by

- `.scratch/natural-replies/issues/04-zeph-reads-replied-to-texts.md`

## Comments
