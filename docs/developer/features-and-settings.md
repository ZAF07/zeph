# Features and Platform Settings

Two ways Admins change how Zeph behaves without a deploy. A **Feature** is an extra that can be switched off. A **Platform Setting** is a value: a number, a prompt, a model, some wording. For the terms, see **Feature** and **Platform Settings** in `CONTEXT.md`.

## Features

### The list

Defined in `FEATURES` in `src/companion/core/features.py`. The keys are the `Feature` enum in `src/companion/core/models.py`.

| Feature | On by default | Needs | User's own switch |
|---|---|---|---|
| Web Search | yes | | |
| Stickers | yes | | |
| Knowledge | yes | | |
| Check-ins | yes | | yes (off until the User opts in) |
| User Memory | yes | | yes (on) |
| Settings in Chat | yes | | |
| Photo Viewing | yes | | yes (on) |
| Personal Stickers | no | Stickers | |
| Curiosities | yes | | |
| Pattern noticing | no | | |
| Pattern exploring | no | Pattern noticing | |
| Pattern sharing | no | Pattern exploring | |

Safety and a User's rights and privacy are never Features (the Safeguard, Crisis Reply, Delete My Data).

**Needs.** A Feature with `needs` works only while the one it needs works. So the Pattern chain is noticing → exploring → sharing. `FEATURES` lists each Feature after the one it needs, so a chain holds.

Curiosities and Pattern noticing also make nothing new while User Memory doesn't work. That is not a `needs`: the Conversation-end steps in `src/companion/core/post_conversation.py` stop early when User Memory doesn't work, so the Users panel doesn't show it as the reason. Pattern noticing also waits until the User presses "Got it" on its notice (`may_keep_observations` in `src/companion/core/observations.py`).

### Does it work for this User?

A Feature works when all of these are true (`status_for` and `feature_statuses` in `features.py`):

1. The **Admin side** is on: the User's own Admin switch if set, otherwise the switch for everyone.
2. Where the User has their **own switch**, it is on (`own_switch_on`).
3. The Feature it **needs**, if any, works.

| Switch | Where it is stored | Who changes it |
|---|---|---|
| For everyone | `feature_switches` table; a Feature with no row uses `on_by_default` | Admin, on the Features page (`/admin/features`) |
| For one User | `user_feature_switches` table: "default", "on" or "off" (`UserFeatureSwitch`) | Admin, in the Users panel. "Default" removes the row |
| User's own | fields on `User`: `user_memory_enabled`, `check_ins.enabled`, `photo_viewing_enabled` | The User, on the Dashboard. User Memory and Photo Viewing can also be changed in chat; Check-ins can only be paused there |

A User can't change their own switch while the Admin side is off. The change raises `FeatureNotAvailableError`, shown as "Not available on your account". The Admin side never changes the User's own switch.

### In code

- In a reply, Check-in tick or Conversation end, ask the snapshot: `snapshot.works(Feature.PATTERN_SHARING)`. `UserSnapshot` is in `src/companion/core/models.py`. `UserSnapshotLoader` in `src/companion/core/user_snapshot.py` reads it once, so a switch changed mid-reply applies from the next one.
- Elsewhere, use `FeatureService`: `works_for(user_id, feature)`, `available_for(...)` (Admin side only) or `require_available(...)`.
- A Move can name a `needed_feature`. The Reply Plan leaves it out when that Feature doesn't work.

### Why it is off

Each status carries a `FeatureReason`: `on_for_everyone`, `on_for_user`, `off_for_everyone`, `off_for_user`, `turned_off_by_user`, or one per needed Feature (`stickers_off`, `pattern_noticing_off`, `pattern_exploring_off`). `needed_feature_off_applied` sets the last kind, using `NEEDED_FEATURE_OFF_REASONS`. The Users panel shows it in plain words from `reasonTexts` in `web/src/lib/features.ts`, e.g. "Off: Pattern noticing is off for this user".

When the Admin side has a Feature off, replies are told so through the `reply_features_unavailable_note` setting, so Zeph can say it if asked. Features with `in_reply_note=False` are left out of that note.

## Platform Settings

### Stored and read

- One row per key in the `platform_settings` table, value as JSON.
- Starting values come from `src/companion/seed/platform_settings.yaml`. At start, `seed_platform_settings` adds only keys that are missing, so an Admin's edit is never overwritten (ADR 0004).
- Each key has a typed `Setting` in `src/companion/core/platform_settings.py`, e.g. `PATTERN_HALF_LIFE_DAYS = Setting("pattern_half_life_days", read_whole_number)`.
- Read with `settings.get(PATTERN_HALF_LIFE_DAYS)`. `PlatformSettings` is read once per reply, tick or Dashboard request; in a reply it is `snapshot.settings`.

Readers: `read_text`, `read_whole_number`, `read_number`, `read_minutes`, `read_hours`, `read_days`, `read_text_list`, `read_on_off`, `read_check_in_gaps`, `read_model_prices`.

### Editable settings

Admins can change a setting only if it has an `EditableSetting` in `EDITABLE_SETTINGS`. Some keys are seed only, e.g. `available_models`, `model_prices`, `welcome_message`.

An `EditableSetting` has a `key`, a `label`, a `kind`, a `hint`, and the rule its value must meet (`minimum`, `maximum`, `max_length`, `required_placeholders`). `PlatformSettingsService.checked_value` checks a save against it.

| Kind (`SettingKind`) | Holds | Example |
|---|---|---|
| `WHOLE_NUMBER` | A number in a range | `pattern_half_life_days` (1 to 3650) |
| `TEXT` | A prompt or wording; may have to keep placeholders such as `{features}` | `reply_plan_prompt`, `crisis_reply` |
| `MODEL` | One of `available_models` | `reply_plan_model` |
| `ON_OFF` | Thinking, or another switch | `reply_plan_thinking` |
| `TEXT_LIST` | A list of words | `pattern_ruled_out_topics` |
| `HOURS_BY_FREQUENCY` | Hours for each Check-in frequency | `check_in_hours_between` |

**Thinking.** A model in `models_that_cannot_think` never thinks, and one in `models_that_always_think` always does. Call `thinking_to_use(settings, MODEL, THINKING)` rather than reading the switch.

**Hints.** Every editable setting has a hint: what it is, what it serves, and which step reads it and when. The API sends it with the value (`GET /api/admin/settings`). `tests/test_admin_settings.py` fails on a missing hint or one over two sentences.

### Where Admins edit them

| Page | Shows |
|---|---|
| Persona (`/admin/persona`) | `persona` (Voice), `persona_outlook` (Outlook) |
| Prompts & models (`/admin/prompts`) | One card per `CoreService` in `CORE_SERVICES`: prompt, model, thinking, extra prompts, limits |
| Safety (`/admin/safety`) | `crisis_reply` |
| Platform settings (`/admin/settings`) | Numbers and switches in sections: Conversations, Memory, Patterns, Curiosities, Knowledge, Check-ins, Photos, Stickers, Data, Web search; then Wording |

The Platform settings page's sections, labels and units are listed by hand in `web/src/components/PlatformSettingsForm.tsx`: `fieldSections`, `textFields`, and `webSearchLimitField` for the Web search section. The Prompts & models page builds its cards from `GET /api/admin/core-services`.

### Eval Variants

A Variant's Setting Overrides change Platform Settings for one Eval Run only (`src/companion/core/evals/setting_overrides.py`):

- Every `EditableSetting` can be overridden. Nothing else to add (`SettingOverrideService.choices`).
- An override is checked like a save on the settings pages (`checked`).
- `variant_settings` puts the overrides on top of the live settings for each case.
- Make Live (`src/companion/core/evals/make_live.py`) writes them to the live settings through the same save (`SettingOverrideService.save_live`).

The Judge's model, thinking and prompts are not Platform Settings, so no Variant can change how cases are marked (ADR 0015). They are seeded from `src/companion/seed/evals/judge.yaml` and edited on the Judge page (`/admin/evals/judge`).

### Prompts

Prompts are text Platform Settings seeded from `platform_settings.yaml`. A new prompt key loads by itself on next start. Changing the text of an existing seed prompt needs a migration that calls `reload_prompt_unless_edited`, never a plain delete, so an Admin's edit is kept (ADR 0029). How: `src/companion/adapters/postgres/migrations/README.md`. Before and after a deploy: `docs/PROMPT_EDITS_AND_DEPLOYS_GUIDE.md`.

## Settings a User changes

These are per User, stored on the `User`, not Platform Settings. The keys are `ChatSetting` in `models.py`: Check-in pause, frequency and quiet hours, User Memory, Photo Viewing, time zone, directness, and noting evidence on a Pattern they disagreed with (`contested_gathering`).

A User changes them on the Dashboard or by asking Zeph in chat (ADR 0006). In chat, `SettingsTools` in `src/companion/core/chat_settings.py` offers LLM tools that call the same core services as the Dashboard. The contested-gathering tool is offered only while Pattern sharing works. With Settings in Chat off, only the tool to delete their data is offered. `record_where_changed` in `src/companion/core/settings_changes.py` stamps each change as made in chat or by an Admin, so the Dashboard can say so.

## Copy

The website's words are **Copy**, not Platform Settings: fixed plain-text slots seeded from `src/companion/seed/copy.yaml`, edited on the Copy page, checked in `src/companion/core/copy.py` (ADR 0019). Anything Zeph says or is told stays a Platform Setting.

## Recipe: add a Platform Setting

Traced from `pattern_half_life_days`.

1. **Seed.** Add the key and its starting value to `src/companion/seed/platform_settings.yaml`.
2. **Typed key.** Add `MY_SETTING = Setting("my_setting", read_whole_number)` in `src/companion/core/platform_settings.py`. `tests/test_setting_keys.py` fails if seed keys and typed keys don't match.
3. **Editable** (if Admins may change it). Add an `EditableSetting(MY_SETTING.key, "Label", SettingKind.WHOLE_NUMBER, minimum=..., maximum=..., hint=...)` to `EDITABLE_SETTINGS`. This also makes it a Setting Override choice for Eval Variants.
4. **Dashboard.**
   - A prompt, model or thinking for a step: add it to that step's `CoreService` in `CORE_SERVICES` (or a new `CoreService`).
   - Anything else: add a field (key, label, unit) to the right section in `fieldSections`, or to `textFields`, in `web/src/components/PlatformSettingsForm.tsx`.
5. **Read it** in core code: `settings.get(MY_SETTING)` on the `PlatformSettings` the step is given (in a reply, `snapshot.settings`).
6. **Tests.** Test the behaviour it changes (e.g. `SCORING_SETTINGS` in `tests/test_pattern_states.py`). Add it to the `settings` fixture in `web/src/components/PlatformSettingsForm.test.tsx` if the page shows it.
7. **No migration** for a new key: the seed adds it on next start. Only changing a seed prompt's text needs one (see Prompts).

## Recipe: add a Feature

1. **Key.** Add it to the `Feature` enum in `src/companion/core/models.py`.
2. **Details.** Add a `FeatureDetails` to `FEATURES` in `src/companion/core/features.py`: name, description, `on_by_default`, `needs`, `in_reply_note`. Put it after the Feature it needs.
3. **If it needs another Feature** with no reason yet: add a `FeatureReason` value in `models.py` and map it in `NEEDED_FEATURE_OFF_REASONS`.
4. **If the User has their own switch:** add a field for it on `User` (and a column on `users`, which needs a migration), read it in `own_switch_on`, and call `require_available` where the User changes it.
5. **Gate the code:** `snapshot.works(Feature.MY_FEATURE)`, or `FeatureService.works_for` outside a snapshot.
6. **Dashboard.** Add the key to the `Feature` type in `web/src/lib/api-client.ts`. For a new reason, add it to `FeatureReason` there and to `reasonTexts` in `web/src/lib/features.ts`. The Features page and Users panel list Features from the API, so they need nothing else.
7. **Tests.** `tests/test_features.py` lists every Feature in order with its default; add yours. Test what changes when it is off.
8. **No migration** for the Feature itself: switches are stored by key as text, and a Feature with no saved switch uses its default. Only a User's own switch (step 4) needs one.
