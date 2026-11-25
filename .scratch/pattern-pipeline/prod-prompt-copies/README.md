# Copy of prod's Reply Plan prompt (25 Nov 2026)

The next deploy runs migrations 0080 to 0101. They drop the stored `reply_plan_prompt`, so the Admin's edited text on prod is replaced by the seed's. See issue 28 in `../issues/archive/`.

- `reply_plan_prompt.prod-2026-11-25.txt`: the edited prompt as stored on prod (25,895 characters, last saved 23 Nov; checked against prod's hash).
- `reply_plan_prompt.seed-at-9d1af553.txt`: the seed text of the release prod runs, to see what the edit changed.

If the prompt is edited on prod again before the deploy, take a new copy first.

## To restore after the deploy

1. Deploy as usual. The Reply Plan prompt on prod is now the new seed text, which has the new Curiosity and Pattern sharing rules.
2. See what your edit changed: compare the two files here.
3. Dashboard → Admin → Prompts & models → Reply Plan → Prompt. Put your changes back into the new text. Don't paste the old prompt over it whole, or the new rules are lost.
4. Save. It applies from the next reply.
5. Send Zeph a message and check the reply reads right.

The other edited prompts (`persona`, `persona_outlook`, `response_prompt`, `understanding_prompt`) are not touched by this deploy.
