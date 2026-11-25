# Keeping your prompt edits across a deploy

For the Admin who edits prompts on the Dashboard and deploys releases.

## The problem in one minute

- A prompt has two homes: the **seed** in the code (`src/companion/seed/platform_settings.yaml`) and the **stored** text on prod, which is what Zeph uses.
- When you edit a prompt on the Dashboard, only the stored text changes.
- When a release changes a seed prompt, a migration decides what happens to the stored text on deploy:
  - **You never edited it:** the new seed text loads. Nothing to do.
  - **You edited it:** your text is kept, the new seed text does **not** load, and the backend log says so. You merge the new text in by hand.
  - **Old migrations (0101 and earlier) are the exception:** they wipe your edit and load the new seed text, with no warning. Take a copy first.

So after a release that changes a prompt you edited, one side is always missing: either the release's new rules, or your edit. The steps below put them back together.

All commands run from the project folder on your own machine.

## Before a deploy

**1. See which prompts you have edited.** Dashboard → Admin → Prompts & models (and Persona). An edited one says "Last saved … by …". An untouched one says "Using the starting values".

**2. See which prompts the release changes.**

```
git fetch origin
git diff origin/production main -- src/companion/seed/platform_settings.yaml
```

If no prompt you edited shows up, deploy and stop here.

**3. Take a copy of each edited prompt the release changes.** Put the setting's key (the name in the seed file, such as `reply_plan_prompt`) in both places:

```
ssh zeph-deploy 'cd ~/zeph && docker compose exec -T postgres sh -c "psql -U \$POSTGRES_USER -d \$POSTGRES_DB -At -c \"select value #>> '\''{}'\'' from platform_settings where key = '\''reply_plan_prompt'\''\""' > .scratch/pattern-pipeline/prod-prompt-copies/reply_plan_prompt.prod-$(date +%F).txt
```

This only reads. Open the file and check it is your prompt.

Copies live in `.scratch/pattern-pipeline/prod-prompt-copies/`. Take a new one if you edit the prompt again before deploying.

## Deploy

Deploy as usual (`docs/DEPLOYMENT_GUIDE.md`).

## After the deploy

**4. Check which side is missing.** Look for the warning:

```
ssh zeph-deploy 'cd ~/zeph && docker compose logs backend 2>&1 | grep "Kept the stored"'
```

| What you see | What is on prod now | What to merge in |
| --- | --- | --- |
| A line naming the prompt | Your edit | The release's changes |
| No line, and the Dashboard says "Using the starting values" | The new seed text | Your edit, from the copy |

**5. Find the text to merge in.**

- **The release's changes:** the diff from step 2 (run it before the deploy, or use the two commits in place of `origin/production` and `main` after).
- **Your edit:** compare your copy with the seed text it was made from. For a prompt key and the commit prod ran before the deploy:

  ```
  git show <old commit>:src/companion/seed/platform_settings.yaml > /tmp/old-seed.yaml
  ```

  Then compare that prompt in `/tmp/old-seed.yaml` with your copy in an editor (in VS Code: select both files → Compare Selected).

**6. Merge on the Dashboard.** Admin → Prompts & models → the service → Prompt.

- Start from what is on prod now and add the missing side to it.
- Never paste a whole old prompt over the new one: that drops the other side again.
- Save. It applies from the next reply.

**7. Check.** Send Zeph a message and read the reply. If the release added a behaviour (say, a new kind of question), check that too.

## If something went wrong

- **You deployed without a copy and the edit is gone.** The text is still in a nightly database backup from before the deploy (`docs/DEPLOYMENT_GUIDE.md`, Backups: kept 7 days on the server, 30 days in R2). Ask Claude to pull that one prompt out of the dump; don't restore the whole database.
- **You pasted over the wrong text.** Your copy and the seed file both still hold their side. Start again from step 6.

## Asking Claude to do it

Claude can do steps 1 to 5 and draft the merged prompt for you to read and paste. Say: "check my prompt edits before the deploy" or "merge my prompt edit after the deploy".

## Open now (25 Nov 2026)

The next deploy runs the old migrations 0080 to 0101, which wipe the edited `reply_plan_prompt`. The copy is already taken: see `.scratch/pattern-pipeline/prod-prompt-copies/README.md`. After that deploy, follow steps 5 to 7 with "your edit" as the missing side. Remove this section once done.
