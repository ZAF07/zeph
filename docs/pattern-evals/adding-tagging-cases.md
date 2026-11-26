# Correcting and adding Tagging cases

How to turn the 44 drafted Tagging cases into your own labels, and add new ones. Do it **after the whole pattern-pipeline PRD is built**; until then the drafts are the defaults.

## Before you start

| What | Why |
|---|---|
| Edit cases on the Dashboard of your **main local stack** (Admin → Evals → Cases → Tagging). | Evals only run there (not in production), and a saved case is used by the next run straight away. |
| When done, ask an agent to copy your cases into `src/companion/seed/evals/cases/tagging.yaml`. | The seed only fills new databases and never changes a case already saved, so editing the file alone does nothing to your stack. |
| Never paste a real User's words. Write a made-up version with made-up names. | The platform has real Users; their words must not end up in test data. |
| Check the estimate before each run (one case ≈ S$0.003, all 44 ≈ S$0.15). | Every run calls the real model and costs money. |

## The parts of a case

| Part | What to put | Why |
|---|---|---|
| Key | Starts with the kind: `conf-`, `ach-`, `ctrl-`, `unclear-`, `nothing-`, `two-types-`, `cond-` (about Conditions). | It can't change later, and runs and the terminal pick cases by it. |
| Life Threads | Only if the moment belongs to an ongoing story. | The tagging step is shown them and links Observations to them. |
| Conversation | 2–4 messages; the telling line in a **User** message. | Code keeps only quotes that are word for word in the User's own texts. |
| Observations to expect | What a careful reader would tag. Empty when there's nothing to tag. | The case passes only when what code keeps is exactly this. |

For each expected Observation:

- **Pattern Type:** its ID from Admin → Pattern Catalog, because the check compares IDs.
- **For or against:** "for" if it matches a sign, "against" if it matches a sign against, because the two count opposite ways in the score.
- **Unclear:** on when two look-alike Pattern Types both fit; put either one. That's how the step should say it can't tell, instead of guessing.
- **Audience, Stakes, State going in:** leave empty to not check one. Pick a value when the User's words say it, or "Must be empty" when they don't and the step must not guess. State going in is how they were before it happened: a feeling afterwards is "Must be empty". The case fails when a kept Observation holds something else, and the result's Conditions line shows what was kept.
- **Anyone would:** on when the other person is a **stranger or someone above the User** (boss, director), for or against. Code decides this from those tags, and today only CONF.AVOID.BELONG has them.

## Correct a drafted case

1. **Read the Conversation fresh and decide what you'd tag**, using the catalog's signs and look-alikes. Your label is the answer key, not the model's output.
2. **Change the expected Observations, or the messages if the case doesn't test what it claims.** A case that tests the wrong thing gives a meaningless score.
3. **Archive any case you can't label with confidence.** A doubtful label teaches nothing.
4. **Run the case and read Expected, Kept by code and Dropped by code.** This shows whether the step agrees with you.
5. **If it fails, don't edit the case to match the model.** Note the failure in issue 20. That failure is the finding; bending the label hides it.

Start with the ones the first run failed (run `4352910b`): the four `conf-situational-…`, `conf-mum-holiday-plans`, the four `unclear-…` and the two `ctrl-anyone-…` cases.

## Add a case from a real situation

1. **Take one real moment and rewrite it as a short, messy made-up chat** (hints, jokes, "it's fine"). Real people aren't textbook examples, so tidy cases flatter the step.
2. **Label it as above and save under a new key.** Use Duplicate on a similar case to start, so it keeps a shape that's known to work.
3. **Run it once and read the result.** This catches a case that can't pass for a reason of its own (e.g. the line is in Zeph's message).

## Keep the set balanced

Give every Pattern Type a clear "for", an "against", an "anyone would" (or a real-crisis case for types that can't be), and an unclear case with each look-alike. Keep plenty of "nothing to tag" cases too. A set that's mostly one kind only tests that kind. Add cases for new Pattern Types as they land (issue 15). The long-term target is 200 labelled Observations.

## When you're done

1. **Run all Tagging cases and note the score.** It's the baseline later prompt changes are compared to.
2. **Ask an agent to copy the cases into `tagging.yaml`.** So fresh databases get your version.
3. **Tick the item in issue 20.** So the PRD's last open step is closed.

Later, a second person labels the same cases without seeing yours. Where you disagree, the case or the Pattern Type's description needs work (see `README.md`).
