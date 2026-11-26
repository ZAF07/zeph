# Model calls: models, prompts, cost and the log

How core code asks a model for something, which provider answers, which settings each step uses, and what is recorded. For what each step is given, see "Prompts: which step uses which" in `docs/message-pipeline/README.md`.

The rule throughout: **the model reads and words; code decides.** The model writes an answer (often JSON). Code checks it, keeps only what passes, and makes every decision that counts.

## How a call is made

Core services never call a provider. They call `UsageRecordingChatModel` (`src/companion/core/usage.py`), which wraps the `ChatModel` and `PhotoViewer` ports (`src/companion/core/ports.py`). For every call it:

- asks the model,
- adds the tokens to the User's Usage,
- writes the call to the Model Call Log, failed calls too.

So no service has to log or count anything itself.

A typical call, from `PatternTagger._ask` in `src/companion/core/observations.py`:

```python
settings = snapshot.settings
for _ in range(2):
    answer = self._chat_model.generate(
        snapshot=snapshot,
        step=ModelStep.PATTERN_TAGGING,
        model=settings.get(PATTERN_TAGGING_MODEL),
        thinking=thinking_to_use(
            settings, PATTERN_TAGGING_MODEL, PATTERN_TAGGING_THINKING
        ),
        instructions=settings.get(PATTERN_TAGGING_PROMPT),
        history=[ChatLine(role=ChatRole.USER, text=description)],
    )
    if read_tagging_answer(answer) is not None:
        return answer
return None
```

`UsageRecordingChatModel.generate` takes `snapshot`, `step`, `model`, `thinking`, `instructions`, `history`, and optionally `tools` and `message_instructions`. It returns the answer text (a `str`). Photos go through `look(snapshot, model, thinking, instructions, photo)`, logged as `ModelStep.PHOTO`.

The port's own `ChatModel.generate` has no `snapshot` or `step`. It returns a `ModelAnswer`: text, `tokens_in`, `tokens_out`, `tool_calls` and `reasoning`.

Three inputs:

| Input | What goes in |
|---|---|
| `instructions` | The step's prompt, with the Persona's voice in front for calls that speak to the User, or its Outlook in front for the Reply Plan. Stays the same from call to call, so a provider can cache it. |
| `message_instructions` | Made for this one call. Only the Reply uses it today. |
| `history` | The Reply gets the Recent Messages as chat turns. Every other step gets one user line: a text code builds for that step (`describe_...` functions; the Safeguard gets a transcript of the Recent Messages). |

Tools are offered to two steps only: the Reply (web search, settings, stickers, photos) and the Reply Plan (`past_day`). The tool loop lives in the adapter, up to `MAX_TOOL_ROUNDS` (4, in `src/companion/adapters/chat_tools.py`), then the model must answer without tools.

## Providers

| Adapter | Where | When |
|---|---|---|
| `OpenRouterChatModel`, `OpenRouterPhotoViewer` | `src/companion/adapters/openrouter/` | The default. Plain `httpx` against OpenRouter's Chat Completions API. |
| `DeepSeekChatModel`, `DeepSeekPhotoViewer` | `src/companion/adapters/deepseek/` | The backup, if OpenRouter is down. Uses LangChain's `ChatDeepSeek`. |

- The switch is manual: `CHAT_MODEL_ADAPTER` in `.env` (`openrouter` or `deepseek`; `load_test` only in a load test), read as `chat_model_adapter` in `src/companion/config.py`. There is no automatic fallback (ADR 0028).
- Keys come from `.env` through `config.py`: `OPENROUTER_API_KEY` and `DEEPSEEK_API_KEY`. Only the chosen adapter's key is needed; a missing one fails at startup (`main.py`).
- OpenRouter uses the operator's own provider keys (BYOK). Each request allows only the model's maker to answer (`provider: {only: [...]}`), and the adapter logs a warning if a reply was paid with OpenRouter credits.
- Model names are saved as OpenRouter names, e.g. `deepseek/deepseek-v4.1-flash-1017`. The DeepSeek adapter turns the two DeepSeek names into direct ones (`to_direct_name`) and refuses any other provider's model.
- Claude models (`anthropic/...`) get prompt caching: the fixed `instructions` are marked with `cache_control`. Other models get no marker.
- The models Admins can pick are the Platform Setting `available_models`.

LangGraph is gone (ADR 0009). `src/companion/adapters/langgraph/` holds only an old `__pycache__`; no code uses it.

## Every model step

Each value of `ModelStep` (`src/companion/core/models.py`). Setting names are keys in `src/companion/core/platform_settings.py`.

| `ModelStep` | What it does | Prompt | Model | Thinking |
|---|---|---|---|---|
| `safeguard` | Checks each text for risk | `safeguard_prompt` | `safeguard_model` | `safeguard_thinking` |
| `understanding` | Reads what the User said, means and feels | `understanding_prompt` | `understanding_model` | `understanding_thinking` |
| `reply_plan` | Forms the Read; picks Need, Moves, what the reply uses | `persona_outlook` + `reply_plan_prompt` | `reply_plan_model` | `reply_plan_thinking` |
| `reply` | Writes the reply, with tools | `persona` + `response_prompt` + sections | `response_model` | `response_thinking` |
| `photo` | Describes a photo | `photo_description_prompt` | `photo_model` | `photo_thinking` |
| `check_in` | A Check-in sent on its own | `persona` + `check_in_prompt` | `check_in_model` | `check_in_thinking` |
| `check_in` | Did the reply bring up its Woven-in Check-in? | fixed in code: `BROUGHT_UP_CHECK_PROMPT` | `check_in_model` | off |
| `conversation_end` | Memory processing and the Day Summary | `memory_processing_prompt` | `memory_processing_model` | `memory_processing_thinking` |
| `life_threads` | Keeps Life Threads | `life_thread_keeping_prompt` | `life_thread_keeping_model` | `life_thread_keeping_thinking` |
| `curiosities` | Keeps Curiosities | `curiosity_keeping_prompt` | `curiosity_keeping_model` | `curiosity_keeping_thinking` |
| `move_outcomes` | Keeps Move Outcomes | `move_outcome_keeping_prompt` | `move_outcome_keeping_model` | `move_outcome_keeping_thinking` |
| `pattern_tagging` | Tags Observations | `pattern_tagging_prompt` | `pattern_tagging_model` | `pattern_tagging_thinking` |
| `patterns` | Keeps Patterns with no Pattern Type | `pattern_keeping_prompt` | `pattern_keeping_model` | `pattern_keeping_thinking` |
| `pattern_matching` | Matches an unmatched Pattern to a new Pattern Type (Admin command) | `pattern_matching_prompt` | `pattern_matching_model` | `pattern_matching_thinking` |
| `pattern_other_side` | Argues the other side before a Pattern is ready | `pattern_other_side_prompt` | `pattern_other_side_model` | `pattern_other_side_thinking` |
| `pattern_shared_check` | Was the Pattern shared? | fixed in code: `SHARED_CHECK_PROMPT` | `check_in_model` | off |
| `prediction_given_check` | Was the Prediction given? | fixed in code: `GIVEN_CHECK_PROMPT` | `check_in_model` | off |
| `curiosity_asked_check` | Did the reply ask its Curiosity? | fixed in code: `ASKED_CHECK_PROMPT` | `check_in_model` | off |
| `settings_claim_check` | Does the reply claim a setting changed when no tool was called? | fixed in code: `CLAIM_CHECK_PROMPT` | `check_in_model` | off |
| `portrait` | Writes the User Portrait | `portrait_prompt` | `portrait_model` | `portrait_thinking` |
| `personal_stickers` | Keeps Personal Stickers | `personal_sticker_keeping_prompt` | `personal_sticker_keeping_model` | `personal_sticker_keeping_thinking` |

Two calls are outside this table, because they are for no User:

- **Knowledge "when it helps" draft** (`src/companion/core/knowledge.py`): `knowledge_when_it_helps_prompt`, `_model`, `_thinking`. It calls the plain `ChatModel`, so it is not in Usage or the Model Call Log.
- **The Eval Judge** (`src/companion/core/evals/judge.py`, run from `runner.py`). It also calls the plain `ChatModel`, so its calls are not in the Model Call Log.

## Thinking

The thinking switch asks the model to think before it answers. OpenRouter gets `reasoning: {enabled: true|false}`. The reasoning text, if any, is kept in the call's content. A Claude model with thinking on may still skip it on an easy call, so empty reasoning is not an error.

Some models can't turn it off or on. Two Platform Settings name them: `models_that_always_think` and `models_that_cannot_think`.

- `thinking_to_use(settings, MODEL_SETTING, THINKING_SETTING)`: for a step with its own switch. On if the model always thinks, off if it can't think, else the saved switch.
- `thinking_for_model(settings, model, wanted)`: the same rule for a call that names its own wish. The fixed checks pass `wanted=False`, so they think only on a model that always thinks.

The adapter holds no model names. A caller that skips these rules can get an OpenRouter error. The Dashboard locks the switch for such models.

## Usage and cost

Per call, `UsageRecordingChatModel` adds `tokens_in` and `tokens_out` to the User's day (`UsageLimiter.record_tokens`). Usage is counts only, on the User's own day: messages, tokens read and written, web searches, and whether a limit turned anything away (`DailyUsage` in `models.py`).

- Admins see it at `/admin/usage`.
- Costs in money are only worked out for Eval Runs, from **Model Prices** (SGD per 1,000,000 tokens in and out, setting `model_prices`). Admins set them at `/admin/evals/costs`. OpenRouter's reported cost is not used.

## The Model Call Log

`ModelCallLog` (`src/companion/core/model_call_log.py`). Calls are grouped into a trace: one per Message, Check-in, Conversation end, Portrait rewrite or pattern matching run (`TraceKind`).

**Kept for every call, every User:** step, model, thinking on or off, start time, time taken, tokens in and out, the error's type if it failed, and the names of the tools called.

**Kept only for Admins' own chats and Eval runs:** the full content (`ModelCallContent`): instructions, history, tools offered, tool calls and results, the answer and the reasoning. Never for other Users (ADR 0010). A photo's image is never kept.

**Shapes**, counts and choices only, never words, set right after the call:

| Shape | On which call |
|---|---|
| `understanding_shape` | Understanding: mood intensity, cause known, struggling, past look-ups |
| `reply_plan_shape` | Reply Plan: the Need, Moves, how many Life Threads, the Read, Check-in Kinds |
| `check_in_shape` | Brought-up check: the Check-in Kind and whether it was brought up |
| `tagging_shape` | Pattern tagging: how many Observations were tagged and dropped |

- Admins see it at `/admin/model-calls`, filtered by User, days, step or errors only (up to 200 traces). One trace opens at `/admin/model-calls/[traceId]`.
- Message Retention removes entries older than the retention period. Delete My Data and Account Deletion remove a User's entries.
- To debug a real User's bad reply, reproduce it in an Admin's own chat or an Eval.
- `MODEL_CALL_DEVELOPER_LOGS=true` prints every call's full content to the backend logs. Local and worktree `.env` only, never production.

## Answers in JSON

Most steps ask for one JSON object. The pattern, from `read_tagging_answer` in `observations.py`:

1. Take the text from the first `{` to the last `}`, so a code fence or a line around it doesn't matter.
2. `json.loads` it. If it fails, or the expected key is missing, return `None`.
3. The caller asks once more (`for _ in range(2)`). If it still can't be read, nothing is kept and a fallback is used.

Then pure functions check each part (`plan_observations`, `check_observation` and the like). The model never decides on its own what is stored, scored or shared. Pattern prompts hold no numbers; numbers are Platform Settings (ADR 0025).

## Prompts

Prompts, models and thinking switches are Platform Settings, seeded from `src/companion/seed/platform_settings.yaml`. Admins edit them at `/admin/prompts` (the Persona at `/admin/persona`); a change applies from the next reply. A migration that changes a seed prompt uses `reload_prompt_unless_edited` (`src/companion/adapters/postgres/prompt_reload.py`), so an Admin's edit is kept. See `src/companion/adapters/postgres/migrations/README.md` and `docs/PROMPT_EDITS_AND_DEPLOYS_GUIDE.md`.

## Other outside calls

- **Web search**: `TavilyWebSearch` (`src/companion/adapters/tavily/web_search.py`), key `TAVILY_API_KEY`. Offered to the Reply as tools by `WebSearchTools` (`src/companion/core/web_search.py`), within `web_search_daily_limit`.
- **Embeddings**: `FastEmbedEmbedder` (`src/companion/adapters/fastembed/embedder.py`) runs **locally** with `BAAI/bge-small-en-v1.5`, downloaded on first use. No key, no cost.

## Testing model code

- **Fakes** in `tests/fakes.py`: `ScriptedChatModel` returns scripted answers per step, told apart by their instructions since the port has no `step` (`script`, `script_pattern_tagging`, `script_safeguard` and so on), records each call (`calls`, `pattern_tagging_calls`, ...) as a `ChatModelCall`, and has safe defaults so a test scripts only what it cares about. Also `FakePhotoViewer`, `FakeEmbedder` and `FakeWebSearch`.
- **Contract tests**: `tests/contract/test_adapter_contracts.py`, marked `contract` (`pytestmark = pytest.mark.contract`). Run with `make contract`. They call the real services with the keys in `.env`. Plain `pytest` skips them (`addopts = "-m 'not contract'"` in `pyproject.toml`).
- **Evals** run the real model on made-up cases. They cost money: ask before running one. See `evals/README.md` and `docs/pattern-evals/README.md`.
