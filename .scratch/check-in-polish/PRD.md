# PRD: Check-in polish — steady Due Times, Woven-in Check-ins, a few times a day, and Admin Check-in tools

Status: ready-for-agent

## Problem Statement

Check-ins work, but they feel off for Users and are a black box for Admins.

**Users**

- Check-ins drift later. The next Due Time is counted from when the last Check-in was decided. Every time one is held back (Quiet Hours, or because the User was chatting), every later one shifts too. A User on "most days" whose Check-in lands at 23:00 gets it at 07:30, then the next one is due 07:30 the day after, and so on. The rhythm they picked slowly slides around the clock.
- A Check-in never comes while the User is mid-Conversation. It waits until the Conversation ends. A User who chats with Zeph often can go a long time without one, and a friend would naturally bring something up while talking anyway.
- The most frequent choice is "most days". A User who wants Zeph to reach out several times a day can't have that.

**Admins**

- Admins can't see when a User's next Check-in is due.
- Admins can't see a User's Check-in settings (frequency, Quiet Hours, pause), and can't change them for a User who has trouble doing it themselves.
- Admins can't make a Check-in go out now, for example to help a User test it or to reach out on purpose.
- Admins can't see that a Check-in is being held back, or why. Held-back Check-ins are not logged, so from the admin side a User just seems to get nothing.

## Solution

**For Users**

- **Due Time** is counted from the previous Due Time, not from when the last Check-in went out. A Held-back Check-in delays only itself. Later ones keep their rhythm.
  - Due Times missed while held back (e.g. a long pause) are not made up.
  - A Due Time never falls within half a frequency gap of the last sent Check-in.
- **Woven-in Check-in:** a Check-in that comes due while a Conversation is open is offered to Zeph's replies. The Check-in model, seeing the current Conversation and Zeph's read of the User, decides whether to weave it in where it fits what's being talked about where it fits what's being talked about, the way a friend drifts onto a side topic, or leaves it out.
  - It is never woven in while the User is struggling or while Check-ins are paused.
  - It can be woven in during Quiet Hours, since the User is already talking.
  - If no reply weaves it in before the Conversation ends, it goes out on its own as usual.
- A fourth **Check-in Frequency**, "A few times a day", with an Admin-set gap (6 hours to start).
- The seed default for the Conversation quiet gap becomes 15 minutes.

**For Admins**

A new **Check-in Schedule** admin page lists every User who opted in to Check-ins. For each one it shows:
- their Due Time
- their Check-in Frequency, Quiet Hours and pause
- whether a Check-in is held back right now, and why

From that page an Admin can:
- **Edit a User's Check-in settings.** This is an **Admin Setting Change**: frequency, Quiet Hours, pause and resume. It changes the User's real settings, is marked "Changed by an Admin" on the User's Dashboard, and the User can change it back.
- **Check in Now.** Select Users and ask for a Check-in straight away. It goes ahead even if a User is paused, in Quiet Hours, too soon after the last one, or has the Check-ins Feature off. The Check-in model may still skip. It is refused, with the reason shown, for a User who hasn't opted in or has no Telegram Connection.

The **Check-in Log** also shows whether each Check-in was woven in, and which Admin asked for one sent with Check in Now.

## User Stories

### Steady Due Times

1. As a User on "most days", I want my Check-ins to keep roughly the same time of day, so that one late Check-in doesn't move all the later ones.
2. As a User whose Due Time falls in my Quiet Hours, I want that one Check-in to wait until my Quiet Hours end without pushing back the ones after it, so that my rhythm stays the same.
3. As a User, I want never to get two Check-ins close together after one was held back, so that it doesn't feel like Zeph is piling on.
4. As a User back from a two-week pause, I want one Check-in and then my normal rhythm, not a burst of the ones I missed, so that resuming feels calm.
5. As a User whose Check-in was skipped, I want the next one to come at my usual rhythm, so that a skip doesn't shift my schedule.
6. As a User who never sees when the next Check-in will come, I want that to stay so, so that Check-ins still feel like a friend reaching out.

### Woven-in Check-ins

7. As a User chatting with Zeph when a Check-in comes due, I want Zeph to bring it up naturally in a reply, so that I still get it without a separate message talking over me.
8. As a User, I want a woven-in Check-in to fit what we're talking about, so that it feels like a natural side topic, not a scripted interruption.
9. As a User venting or struggling, I want Zeph never to weave a Check-in in, so that my hard moment isn't interrupted.
10. As a User who paused Check-ins, I want none woven into replies either, so that my pause means what it says.
11. As a User chatting late at night inside my Quiet Hours, I'm fine with a Check-in being woven in, since I'm already talking.
12. As a User, if Zeph never finds a good moment during our Conversation, I want the Check-in to come on its own after the Conversation ends, so that it isn't lost.
13. As a User, I want a woven-in Check-in to show in my "Recent check-ins" like any other, so that my history is complete.
14. As a User who is chatting, I want a woven-in Check-in never to count as one I ignored, so that I'm not asked "would you like fewer?" while I'm clearly talking.
15. As a User, I want at most one Check-in woven into a reply, so that a reply doesn't turn into a list of topics.

### A few times a day

16. As a User who likes frequent contact, I want to choose "A few times a day", so that Zeph reaches out more than once a day.
17. As a User, I want to pick it on my Dashboard Check-ins page, so that it's as easy as the other choices.
18. As a User, I want to tell Zeph in chat "check in with me a few times a day", so that I don't have to open the Dashboard.
19. As a User on "A few times a day", I want my Quiet Hours still respected, so that frequent Check-ins never wake me.
20. As an Admin, I want to set the gap for "A few times a day" in Platform Settings like the other frequencies, so that I can tune how often that is.

### Seeing the Check-in Schedule

21. As an Admin, I want a Check-in Schedule page listing every User who opted in, so that I can see Check-ins across the platform at a glance.
22. As an Admin, I want each User's Due Time shown both as "in 3 h" and in the User's local time, so that I know roughly when they'll hear from Zeph.
23. As an Admin, I want each User's frequency, Quiet Hours and pause shown, so that I understand why their Due Time is what it is.
24. As an Admin, I want to see when a User is held back right now and why (paused, Quiet Hours, no Telegram Connection, waiting to be woven in, today's message limit used up, no Kind to send), so that I can tell why someone isn't hearing from Zeph.
25. As an Admin, I want to see until when it is held back where that's known (e.g. "until 07:30"), so that I know when it will clear.
26. As an Admin, I want a User who is due and not held back shown as "due now", so that I can tell they'll get one on the next tick.
27. As an Admin, I want to search the list by name or email and page through it, so that it stays usable with many Users.
28. As an Admin, I want the page to say when the Check-ins Feature is off for a User, so that I don't wonder why nothing goes out.
29. As an Admin, I want the page to show no message content, so that Users' privacy is kept.

### Admin Setting Changes

30. As an Admin helping a User who can't change their settings, I want to change their Check-in Frequency, so that they get the rhythm they asked for.
31. As an Admin, I want to change a User's Quiet Hours, so that I can fix them for a User in a time zone or routine they struggle to set up.
32. As an Admin, I want to pause a User's Check-ins for a day, a week or until resumed, and to resume them, so that I can help a User who asked for a break.
33. As an Admin, I want my change to take effect the same way as the User's own change would (e.g. changing Quiet Hours that hold a Check-in back decides it again straight away), so that there's one set of rules.
34. As a User, I want to see "Changed by an Admin" next to a setting an Admin changed, so that I know why it isn't what I last set.
35. As a User, I want to change a setting an Admin changed back whenever I like, so that my settings stay mine.
36. As a User, I want the "Changed by an Admin" mark to go once I change that setting myself, on the Dashboard or in chat, so that the mark only shows the latest change.
37. As an Admin, I want to be unable to opt a User in to Check-ins, so that nobody gets unprompted messages they didn't choose.
38. As an Admin, I want to use the existing per-User Check-ins Feature switch to stop a User's Check-ins, so that there's one way to do it.

### Check in Now

39. As an Admin, I want to select one or more Users on the Check-in Schedule and press "Check in now", so that they get a Check-in on the next tick.
40. As an Admin, I want Check in Now to go ahead even if the User is paused, in Quiet Hours, too soon after the last one, or has the Check-ins Feature off for them, so that "now" really means now.
41. As an Admin, I want the Check-in model still able to skip (e.g. the User asked for space), so that Zeph never sends something clearly unwelcome.
42. As an Admin, I want Check in Now refused for a User who hasn't opted in, with the reason shown, so that Users who said no to Check-ins never get one.
43. As an Admin, I want Check in Now refused for a User with no Telegram Connection, with the reason shown, so that I know it can't reach them.
44. As an Admin, I want a Check in Now for a User who is mid-Conversation to become a Woven-in Check-in, so that it doesn't talk over them.
45. As an Admin, I want the User's next Due Time to be one frequency gap after a Check in Now, so that they aren't sent another soon after.
46. As an Admin, I want a User's pause and other settings left as they were after a Check in Now, so that only that one Check-in gets through.
47. As an Admin, I want to see on the Check-in Schedule that a Check in Now is waiting for a User, so that I don't press it twice.

### Check-in Log

48. As an Admin, I want the Check-in Log to show when a Check-in was woven in, so that I can tell the two apart.
49. As an Admin, I want the Check-in Log to show which Admin asked for a Check in Now, so that a Check-in sent during Quiet Hours or a pause is explained.
50. As an Admin, I want the log still never to show message text, so that Users' privacy is kept.

### Admins looking under the hood

51. As an Admin, I want the Model Call Log to show the woven-in Check-in step under the Message, with whether it chose to weave one in and which Kind, as shape only, so that I can debug why one was or wasn't woven in.
52. As an Admin, I want evals that cover weaving a Check-in in and leaving it out, so that I can check the behaviour before changing prompts.
53. As an Admin, I want the woven-in Check-in decision to have its own prompt I can edit, separate from the standalone Check-in prompt, so that I can tune the two jobs separately.
54. As a User, I want the Check-in decision to know my User Portrait, so that Check-ins, woven in or standalone, fit who I am.
55. As a User, I want the woven-in Check-in to know what Zeph already raised or chose to leave alone in this Conversation, so that it doesn't repeat or poke at it.

### Reliability

56. As a User, I want never to get the same Check-in twice, even when it's woven in and saving fails, so that the existing "never twice" promise holds.
57. As an Admin, I want each scheduler tick to read the same number of times however many Users are due, so that it scales with many Users.
58. As an Admin, I want a woven-in Check-in logged only when the reply carrying it was actually sent, so that the log matches what the User saw.

## Implementation Decisions

### Due Time (core, Check-in decision)

- The next Due Time after a sent or skipped Check-in is the first of "previous Due Time + n × gap" that is still in the future. It is then pushed to "last sent Check-in + half a gap" if it would fall earlier. The half-gap is fixed, not Admin-set.
- The minimum is measured from the last *sent* Check-in (woven in or not). Skips send nothing, so they don't count.
- A Check in Now sets the next Due Time to "decided at + gap".
- The previous Due Time is the one held on the User at decision time. A User with none (e.g. just opted in, or just resumed from an until-resumed pause) keeps today's behaviour for setting a first one.
- These rules stay pure functions in the existing Check-in decision module, next to the existing next-due helpers.
- No backfill: the platform isn't live, and the new rule applies from each User's next decision.

### Held back, and why (stored, current only)

- When a tick holds a User back, it saves the reason, and when known the time until, together with the new Due Time, in the same bulk write it already does. Any decision (sent, skipped, ask about fewer) clears it. No history is kept.
- Mid-Conversation is no longer a held-back reason in the domain sense. The tick still doesn't send a standalone Check-in while a Conversation is open. It saves the state "waiting to be woven in" with a retry at the time the Conversation could end, and the Due Time stays as it is.
- A User who changes the setting that held them back is decided again straight away, as today. The saved reason is replaced on the next tick.

### Woven-in Check-ins (core, reply flow — ADR-0009)

- The Check-in model decides, not the Understanding. The Understanding and its prompt are unchanged, so the two keep separate jobs.
- After the Understanding, the code checks all of these:
  - the User's Check-in is due (Due Time passed, or a Check in Now waiting)
  - Check-ins work for them (opted in and Feature on, or a Check in Now)
  - they are not paused (a Check in Now gets past a pause)
  - the Understanding says they are not struggling

  If any check fails, no call is made. This is a code rule, not a model choice.
- If all pass, it makes a woven-in Check-in call. It runs alongside the Understanding's look-ups, so the reply waits as little as possible. The call uses:
  - the Check-in model setting (model and thinking), shared with standalone Check-ins
  - its own new Admin-editable prompt in Platform Settings (ADR-0004), separate from the standalone Check-in prompt, because "slip it into a chat that's going" is a different job from "reach out first"
- The call is given:
  - Persona and the User's local time
  - their recent Check-ins
  - their User Portrait, Memory Items and newest Conversation Summaries
  - the current Conversation's messages
  - this message's Understanding (mood, struggling, Need, reminded Life Threads, what was brought up or left alone)
  - the Kinds that may go: only Kinds without fixed behaviour. Photo and Curiosity Kinds are left out, since the reply already raises Curiosities and sends Shared Photos back by its own rules.
- Its answer is either "weave in" with one Kind's exact name and a one-line note on what to bring up, or "not now". An unknown Kind or an unusable answer is read as "not now".
- On "weave in", the reply call is given the Kind's description and the note, with an instruction to weave it in naturally, at most one per reply.
- The standalone Check-in model is also given the User Portrait from now on, so both Check-in decisions see the User the same way.
- Once the reply is sent, in one transaction (ADR-0008), a Check-in is saved:
  - outcome sent, the Kind, marked woven in, and the requesting Admin if it came from a Check in Now
  - the Due Time is moved on by the rules above
  - any Check in Now request is cleared
- If the reply isn't sent, nothing is logged and the Check-in stays due.
- Reply detection: the User's next message counts as its reply, using the existing reply-window logic.
- The Ignore Threshold count skips woven-in Check-ins: they never add to "ignored in a row".
- Quiet Hours don't stop weaving in. A pause does, except for a Check in Now.
- The standalone Check-in prompt is unchanged. Only its input gains the User Portrait.

### A few times a day

- Add a fourth Check-in Frequency, `a_few_times_a_day`.
  - Dashboard label: "A few times a day".
  - Chat wording: "at most a few times a day".
- The chat settings tool for changing the frequency accepts it (ADR-0006).
- The Platform Setting for gaps by frequency gains `a_few_times_a_day: 6` hours.
  - A data migration adds it to the stored value where it's missing, because reading the gaps fails when a frequency is missing.
  - The admin Platform Settings page shows and edits it.
- The frequency column is plain text, so it needs no schema change.

### Conversation quiet gap default

- The seed default for the Conversation quiet gap becomes 15 minutes. This applies to fresh databases. Existing stored values are not changed, since the owner already set 15.

### Admin Setting Change

- A new core operation lets an Admin change another User's Check-in Frequency and Quiet Hours, and pause or resume them. It reuses the same Check-in service rules the User's own changes use (Due Time recalculated or decided again straight away, as today).
- It records each changed setting as "changed by an Admin" alongside the existing "changed in chat" marks.
- A change by the User (Dashboard or chat) clears the admin mark for that setting. A chat change sets the chat mark instead.
- Turning a User's Check-ins on or off is not offered. Stopping them is the existing per-User Feature switch.
- The User's own Check-ins page shows "Changed by an Admin" next to each marked setting.

### Check in Now

- A new core operation takes a list of User ids and the requesting Admin, and returns a result for each:
  - **requested**: the request is saved on the User along with the Admin who asked, and the Due Time is set to now.
  - **refused: not opted in**
  - **refused: no Telegram Connection**
- The tick loads Users who are due *or* have a Check in Now waiting, including those with the Check-ins Feature off, in the same bulk read.
- For a User with a Check in Now waiting, the decision goes past the Feature switch, pause, Quiet Hours, the half-gap minimum, the Daily Message Limit skip and the Ignore Threshold "would you like fewer?" step. It goes straight to the Check-in model, which may send or skip.
  - Mid-Conversation it waits to be woven in, as above.
  - If the User has since lost their Telegram Connection, it is held back with that reason and the request stays.
- The saved Check-in records the requesting Admin. The request is cleared on any decision.
- Pause and other settings are left as they were.

### Check-in Log

- Each saved Check-in gains "woven in" (yes/no) and "requested by" (an Admin, or none).
- The admin log response and page show both, with the Admin's name.
- Still never the message text.

### Model Call Log (ADR-0010)

- The woven-in Check-in call shows as a Check-in step under that Message's trace. Its shape (every User) is how many Kinds were offered, and whether it chose "weave in" or "not now" and which Kind. Full content stays limited to Admins' own chats and Evals.

### Schema (Postgres adapter)

New columns on the user's Check-in state:
- held-back reason
- held-back until
- Check in Now requested by (Admin user id)
- Check in Now requested at
- "settings changed by an Admin" marks, stored like the existing chat marks

New columns on Check-ins:
- woven in
- requested by

All of these are covered by Delete My Data through the existing per-User tables, and the existing "every per-User table" deletion test must keep passing.

### API and Dashboard (ADR-0012)

Admin API:
- List the Check-in Schedule (search, paged). Each row has:
  - the User's name and email
  - Due Time, and the User's local Due Time
  - frequency, Quiet Hours and pause
  - whether the Check-ins Feature works for them
  - the held-back reason and until when
  - whether a Check in Now is waiting
- Change a User's Check-in settings.
- Pause or resume a User.
- Check in Now for a list of Users, returning the result for each.

User API: the Check-ins page response gains the "Changed by an Admin" marks and accepts the new frequency.

Dashboard:
- A new admin "Check-in Schedule" page, built from the admin design's table and side-panel patterns, with:
  - a row checkbox and a "Check in now" action that shows each User's result
  - a side panel to edit one User's settings
- The admin nav gains the page next to Check-in Log and Check-in Kinds.
- The User's Check-ins page gains the new frequency option and the "Changed by an Admin" marks.
- All calls go through the API client. No business logic in the Dashboard.

## Testing Decisions

- Good tests check behaviour someone can observe: what the API returns, what reaches the fake chat channel, what the Check-in Log shows and when the next Check-in goes out. They don't check internal calls or private helpers.
- **Main seam: the backend end to end.** Drive the real app through its HTTP API, the Telegram webhook and scheduler ticks, with the existing fakes (fake clock, fake scheduler, scripted chat model, fake chat channel) and a real test database. Prior art: the existing Check-in sending, hold-back, daily-limit, send-failure, admin Check-in and settings-via-chat tests.
  - Due Times keep their rhythm after a Quiet Hours or Conversation hold-back. A long pause doesn't produce a burst. The half-gap minimum holds. A skip doesn't shift the rhythm.
  - Woven-in Check-ins:
    - due mid-Conversation → woven into the reply and logged as woven in
    - no woven-in Check-in call at all while struggling or paused
    - the call is given the current Conversation, the Understanding and the User Portrait
    - "not now" or an unusable answer → nothing woven in, still due
    - the standalone Check-in call now gets the User Portrait
    - allowed in Quiet Hours
    - goes out on its own after the Conversation ends when none was woven in
    - never counted toward the Ignore Threshold
    - not logged when the reply fails to send
    - fixed-behaviour Kinds never offered
  - "A few times a day" via Dashboard and via chat. The migration adds the missing gap.
  - Admin Setting Changes change the User's real settings, show "Changed by an Admin", and are cleared by the User's own change. An Admin can't opt a User in. Non-Admins are refused.
  - Check in Now:
    - goes past pause, Quiet Hours, the Feature switch, the half-gap, the daily-limit skip and the Ignore Threshold
    - the model may skip
    - refused for not opted in and for no Telegram Connection
    - woven in mid-Conversation
    - next Due Time is one gap later
    - the log shows the Admin
  - The Check-in Schedule shows Due Times, settings, held-back reasons with until-times, and waiting Check in Now requests.
  - The tick's reads stay flat as due Users grow, including Users with a Check in Now waiting. Prior art: the existing reads-per-tick test.
- **Pure Check-in decision functions**, only for Due Time edge cases that would be clumsy end to end: several missed Due Times, the half-gap pushing a Due Time, Quiet Hours across midnight, a first Due Time with no previous one. Prior art: the existing Check-in decision tests.
- **Dashboard component tests** (Vitest + React Testing Library): the Check-in Schedule table, selection and Check in Now results, the settings side panel, and the "Changed by an Admin" marks and new frequency option on the User's Check-ins page. Prior art: the existing admin Users component tests.
- **Evals:** add eval cases for the woven-in Check-in decision: weave in when it fits, "not now" when the moment is wrong. The struggling and paused cases are code rules, covered by tests, not evals. Existing Understanding evals don't need re-running, since the Understanding is unchanged. Eval runs cost money: confirm with the user before running them.

## Out of Scope

- Fixed daily Check-in times, or Users choosing an exact number per day.
- An Admin-set half-gap minimum.
- A history of Held-back Check-ins.
- Admins turning a User's own Check-ins switch on or off.
- An admin page per User beyond the Check-in Schedule side panel.
- Showing Users when their next Check-in will come.
- Changing the stored Conversation quiet gap on existing databases.
- Weaving photo or Curiosity Kinds into replies.
- Logging refused Check in Now attempts (the Admin sees the reason at the time).

## Further Notes

- Domain terms added or changed in `CONTEXT.md` during grilling: Due Time, Woven-in Check-in, Check-in Frequency, Check in Now and Admin Setting Change (new); Check-in, Quiet Hours, Check-in Pause, Held-back Check-in, Skipped Check-in and Check-in Log (updated).
- Defaults chosen without asking, which are easy to revisit:
  - the half-gap is fixed
  - refused Check in Now attempts aren't logged
  - a Check in Now also goes past the Daily Message Limit skip and the Ignore Threshold step
  - fixed-behaviour Kinds aren't woven in
- Scale: Check-in Schedule reads are paged, and tick reads stay bulk with no per-User queries.
- Related ADRs: 0003 (ports and adapters), 0006 (settings in chat), 0008 (transactions), 0009 (plain core reply flow), 0010 (Model Call Log content), 0012 (TanStack Query).
