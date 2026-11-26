# 01 — Ideas from two memory papers: knowing what changed, and using memory well

Status: needs-triage
Blocked by: none

> **Grilling first.** When the owner picks this issue up, run a grilling session (`/grill-with-docs`) before any code. That session decides which ideas below to build, settles the open questions and splits the approved ones into agent-ready issues. Nothing here is decided yet; the recommendations are a starting point.

## Parent

None. Comes from a review on 26 Nov 2026 of two research papers against how Zeph works (`ABOUT.md`, `docs/message-pipeline/README.md`, `CONTEXT.md`). Goal: a more engaging, natural and intentional chat, keeping only what fits Zeph's purpose and principles, not following the papers wholesale.

## The papers

Read them again to confirm the findings below; page numbers are PDF pages.

| Paper | arXiv | Local PDF | Plain text (pulled out with pypdf) |
|---|---|---|---|
| HorizonBench: Long-Horizon Personalization with Evolving Preferences (Li et al., v2 Nov 2026) | https://arxiv.org/abs/2604.17283 | `.scratch/memory-from-papers/papers/horizonbench-2604.17283.pdf` | `.scratch/memory-from-papers/papers/horizonbench-2604.17283.txt` |
| We Are What We Remember: Mental-State-Driven Memory for Long-Term Character Dialogue (MindMem, Jia et al., v2 Nov 2026) | https://arxiv.org/abs/2611.16223 | `.scratch/memory-from-papers/papers/mindmem-2611.16223.pdf` | `.scratch/memory-from-papers/papers/mindmem-2611.16223.txt` |

The Read tool can't show these PDFs here (poppler isn't installed); read the `.txt` files, or pull the text with pypdf. MindMem's Figures 1–3 are images, so they are missing from its text.

## What the papers found

### HorizonBench

- **The failure:** a life event the User mentions (a new job, a diagnosis) changes what they want, but they never say the new preference. All 25 frontier models tested kept serving the old one more often than chance would predict; the best scored 52.8% (p7–8). Reasoning models did no better (p8).
- **It is worse when the old preference was said recently** (0–14 days before: 47.7% of wrong answers pick the old value, p8), and when it was said outright (p8).
- **Retrieval made it worse.** BM25, two dense retrievers (384- and 1536-dimension, within 0.8 points of each other) and the latest 10 turns all scored below reading the full history. The event turn never names the preference, so it doesn't look similar to the question (p9).
- **Memory tools didn't fix it.** Mem0 matched the full history. A note-taking memory agent told to "record any preference that changed and why" scored 5.5–16 points worse (p9, p21).
- **What worked:** one sentence in the input saying the change ("after {event}, my preference changed: … is now …") added 11–22 points; a paraphrase that never names the new value got most of that gain; an unrelated sentence did nothing (p21, Tables 15–16).
- **Their conclusion:** remembering what a User said and knowing what they want now are separate skills (p2, p10).
- **How often preferences shift** (human study, p4–5, p15–18): 17.5% of real life events moved 2–5 of 6 ratings by 3+ points on a 1–7 scale; with a 1-point bar, 69.6%. Caveat: 160 people, aged 18–39, 86.9% work in data annotation or AI training.
- **Reusable:** generator prompts and data formats in Appendix J (p22–25); code and data at github.com/stellalisy/HorizonBench.

### MindMem

- **The failure:** similarity search brings up topically close memories and misses ones that matter. "I feel low" brings up "prefers solitude" and the character withdraws, instead of a gentle check on the job interview that is worrying them (Fig. 1, p2).
- **Their design:** a store of raw episodes, plus 40 "slot" notes (Tables A1–A2, p12–13), each linked to the episodes it came from. A per-turn reasoner reads every slot, writes a short thinking line, picks slots, and code follows the picked slots' links back to their episodes, so evidence arrives that similarity never found (p4, p12).
- **Ablation:** removing that active recall drops them to baseline level (SMR 59.0 → 29.7). A trained small reasoner beats a general model by 17 points (Table 4, p9).
- **Knowing vs using:** of 100 failures, 64 had the right memory in the input but the reply didn't use it; 36 never reached the reply (p7). Even gold memories injected directly scored only 50.7 on use (p6–7).
- **Their benchmark's rule for real memory use (p5, p14, p22):** the reply uses the memory through a detail, plan or boundary that couldn't be guessed from the current message. Echoing the trigger, generic empathy, length, explicit "I remember…" mentions and extra intimacy don't count.
- **Other rules worth noting:** observations kept apart from interpretations; per-turn inferences never written back as evidence; a situational state can sit beside a general one ("wants company during interview prep" beside "likes solitude"); open loops can be closed or cancelled (p3, p12–13).
- **Their stated risks (p8–9):** inferring needs and adapting closeness can create unwanted intimacy or dependence; don't present inferences as diagnosis; let users correct or remove what is kept.
- **Caveat:** tested on role-play characters, not reflective companion chat. Prompts in the appendix (p18–23); code at github.com/jiazhicheng7-ctrl/MindMem.

### The 40 slots, against Zeph

| Group | What it holds | In Zeph |
|---|---|---|
| User (12) | real-life context, history, goals, life and interaction preferences, psychological patterns, what support works, self-view, + 4 story/romance tastes | Mostly covered: Memory Items, Goals, Life Threads, Patterns, Move Outcomes, directness, User Portrait. The 4 story/romance slots don't apply. |
| Avatar (3) | the fictional character the User plays | Not used: Users talk as themselves. |
| Role (10) | the AI character's identity, backstory, values, motives, habits, voice, affection style, social circle, **learned and updated from chats** | Zeph's Persona (voice) and Outlook are fixed, Admin-written, the same for every User, and the Persona forbids a made-up life. So most of this needs no memory. Gap: what Zeph has said it thinks to this User (idea 6). |
| Relationship (10) | what the bond is, stage, state, shared rules and boundaries, turning points, milestones, contributions, gifts, lasting feelings, unfinished business | Partly: topics asked to drop, directness and Familiarity; commitments, Curiosities and Predictions are the unfinished business. Gaps: shared rules, turning points (idea 7). |
| Emotional event (1) | big emotional moments | Covered: Day Summaries carry feeling; Life Threads. |
| Group (1) | alliances in group chats | Not used: Zeph is one to one. |
| Story world (3) | rules and history of a made-up world | Not used: real world. |

## Where Zeph stands today

- **Recall** is more than plain similarity: pgvector cosine search with a small local model (`BAAI/bge-small-en-v1.5`, 384-dimension, through fastembed), on what the Understanding says the User means plus their latest texts, with a closeness bar; Threads also match on people or things named; Patterns come in through linked Threads and by closeness; what comes to mind stays in mind for the Conversation; the Reply Plan picks what the reply uses.
- **Memory Items** hold only their text and dates; a changed fact replaces the old one (`CONTEXT.md`). **Move Outcomes** have `made_at`, not shown to the Reply Plan.
- **Already in line with the papers:** said / read / unclear in the Understanding; guesses are Curiosities, never User Memory (ADR-0017); the Reply Plan already does the MindMem reasoner's job; Pattern narrowing is the same idea as situational states (ADR-0031).

## The ideas

Each with the recommendation from the review. The grilling decides.

1. **A life event may change what Zeph knows** (HorizonBench). When a Conversation shows a big life event, raise a guess Curiosity (aim `guess`, ADR-0026) for each Memory Item or Move Outcome it may change, linked to that item. When building the Reply Plan's input, code writes beside the item "may have changed since <event> (<date>); checking". The item itself is untouched, so the User never sees a guess (ADR-0017 rejected a certainty marker on Memory Items). Once they answer, the Curiosity closes and the Memory Item step updates the item or leaves it. Fits Zeph's heart: noticing that someone changed is itself worth telling them.
   - Open: what counts as a big life event, and which step spots it (Life Thread keeping or Curiosity keeping)? How are Curiosities linked to an item (new link)? Does it apply to Patterns too, or do Observations against already cover that?
2. **Big recent stories and open commitments always come to mind** (MindMem). Open Life Threads with a big event in the last few weeks, plus open commitments, come into Recall on every reply, close in meaning or not, so "I feel low" reaches the interview. Plain code, cheap. A bigger embedding model is not the fix (HorizonBench p9).
   - Open: how recent and what counts as big; does it crowd `life_threads_per_reply`; the existing hold-backs (brushed off, asked to drop) must still apply.
3. **A Memory Use Eval** (MindMem's SMR). Each case gives history plus a trigger that doesn't hint at the memory; the Judge checks whether the reply was shaped by it (a detail, plan or boundary that couldn't be guessed from the message), with no credit for callbacks, length or warmth, and fails a forced "remember when…". Tests the step from Reply Plan pick to Reply, our likely weak spot too. Best built first, to measure ideas 1, 2 and 5 before and after. Evals cost money: run only on demand.
   - Open: a new Eval case shape (ADR-0013, ADR-0014); how many starting cases; does the Judge see the target memory privately, as MindMem's does.
4. **Memories that hold only in some situations** (MindMem p3). A Memory Item can carry an optional "while…", so "wants company while prepping for interviews" sits beside "generally likes solitude" instead of replacing it. Same idea as a Pattern's narrowing (ADR-0031).
   - Open: one Memory Item with a scope, or two; how the Dashboard shows it; does the Memory Item step get it right.
5. **Use memory, don't recite it** (MindMem p14). One line in `response_prompt`: let what you remember shape what you say, and mention it only when that helps them. Reload through `reload_prompt_unless_edited` (ADR-0029). Check with idea 3.
6. **Zeph's own views stay consistent** (MindMem's Role slots). The Persona says Zeph "has real views and says them". What Zeph told this User it thinks ("I think you're too hard on yourself") is kept past the 24-hour Recent Messages, so it doesn't contradict itself weeks later.
   - Open: where it lives (a Life Thread's story, the Day Summary, or something new), and does it overlap Reads already saved in Reply Plans.
7. **Shared rules and turning points** (MindMem's Relationship slots). Keep how the User wants Zeph to be with them ("blunt about work, never about family") and the moments that changed things ("the day they agreed with the people-pleasing Pattern"), for a more continuous chat. **Left out on purpose:** relationship stage, affection, gifts, lasting feelings. They push toward intimacy and dependence, which `ABOUT.md` rules out, and MindMem's own ethics section warns about it (p9).
   - Open: overlap with directness, topics asked to drop and Move Outcomes; does the User see these on the Dashboard (they should, as User Memory); may merge with idea 6.

## Not taking

- Training a small model to pick memories (MindMem's Mind): the Reply Plan does that job.
- MindMem's 40-slot schema as a whole: much is role-play only (avatar, story world, groups).
- Relationship stage, affection, gifts, lasting feelings: against "no emotional dependency".
- A bigger embedding model, Mem0, or a note-taking memory agent: HorizonBench shows none fixes this.

## Acceptance criteria

- [ ] A grilling session with the owner has decided, for each of the seven ideas, build, change or drop, with the reason recorded here under `## Comments`
- [ ] The findings above were checked against the papers, and any that were wrong are corrected here
- [ ] Decisions that move the domain model are in `CONTEXT.md` and new ADRs (e.g. a change to ADR-0017's line on Memory Items)
- [ ] Each approved idea is its own agent-ready issue in `.scratch/memory-from-papers/issues/`, with `Blocked by:` set, the Memory Use Eval first if it is approved
- [ ] This issue is then marked completed and archived

## Comments
