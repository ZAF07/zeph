# PRD: Model calls through OpenRouter

Status: ready-for-agent

## Problem Statement

Every model call the Companion makes goes straight to DeepSeek through one DeepSeek adapter. Admins can only pick DeepSeek models in Prompts and models, and trying any other model (Claude first) means writing a new adapter for each provider. The operator now has an OpenRouter account with their own Anthropic and DeepSeek keys added (BYOK), and wants one way in to every model, so that a new model is only a new name in Platform Settings.

## Solution

Model calls go through OpenRouter by default, using the operator's own provider keys. A new OpenRouter adapter sits behind the existing `ChatModel` and `PhotoViewer` ports, so no core service changes. Admins pick OpenRouter model names (e.g. a DeepSeek model and a Claude model) in Prompts and models, and the model an Admin saves is the model the next call uses. The thinking switch works for every model, and the reasoning text is kept in the Model Call Log as it is today. Claude calls use prompt caching. The direct DeepSeek adapter stays as a backup the operator can switch back to with one setting.

## User Stories

1. As an Admin, I want to pick a Claude model for a core service in Prompts and models, so that I can try Claude without a code change.
2. As an Admin, I want to pick a DeepSeek model for a core service in Prompts and models, so that services I keep on DeepSeek keep working.
3. As an Admin, I want the model I save for a core service to be the model its next call actually uses, so that what I see in settings is what runs.
4. As an Admin, I want a model change to apply from the next reply or Check-in, with one already under way finishing as it started, so that it matches how every other Platform Setting behaves.
5. As an Admin, I want the thinking switch for a core service to turn thinking on or off for whichever model it uses, so that the switch means the same thing for DeepSeek and Claude.
6. As an Admin, I want to see a model's reasoning in the Model Call Log when thinking is on, so that I can understand why it answered as it did.
7. As an Admin, I want the Model Call Log to show the exact model name each call used, so that I can confirm a change took effect.
8. As an Admin, I want tokens in and out recorded for OpenRouter calls as they are today, so that usage stays visible.
9. As an Admin, I want the list of models I can pick to contain OpenRouter names, so that I can only save models the system can call.
10. As an Admin, I want saving an unknown model name to be refused with a clear message, so that a typo can't break replies.
11. As an Admin, I want Model Prices keyed by the new model names, so that Eval Run estimates and totals keep working.
12. As an Admin, I want the eval judge model to use an OpenRouter name too, so that Eval Runs keep working after the switch.
13. As an Admin, I want any model I already chose for a core service kept (only renamed to its OpenRouter name), so that the switch doesn't undo my settings.
14. As a User, I want replies to keep coming the same way after the switch, so that I don't notice any change.
15. As a User, I want the Companion to still look at my photos, so that photo replies keep working through OpenRouter.
16. As a User, I want the Companion's tools (web search, settings in chat, look-ups) to keep working, so that it can still do what it does today.
17. As a User, I want a model error to be handled as it is today, so that I'm never left with a broken reply.
18. As the operator, I want every OpenRouter call to use only my own provider keys, so that it never spends OpenRouter credits.
19. As the operator, I want Claude calls to use prompt caching, so that long repeated prompts cost less.
20. As the operator, I want to see whether the cache was used, so that I can check caching actually works.
21. As the operator, I want to switch back to the direct DeepSeek API with one setting, so that I have a way out if OpenRouter is down.
22. As the operator, I want my OpenRouter key read from `.env` through config like every other key, so that no secret lands in code.
23. As the operator, I want a clear error at startup if the chosen adapter's key is missing, so that a bad deploy fails fast.
24. As the operator, I want Claude calls that use tools while thinking to keep working across tool rounds, so that tool use doesn't break on Claude.
25. As the operator, I want contract tests against the real OpenRouter API, so that I can confirm it works before shipping.
26. As a developer, I want the OpenRouter adapter to need no core changes, so that the ports-and-adapters design holds.
27. As a developer, I want the adapter tested with fake OpenRouter replies, so that tests are fast and free.

## Implementation Decisions

- **New OpenRouter adapter** implementing `ChatModel` and `PhotoViewer`, built on plain `httpx` against OpenRouter's Chat Completions API, not LangChain. Plain HTTP keeps full control of the request (`reasoning`, `cache_control`, provider routing) and reads the reply JSON directly, so the reasoning text isn't dropped. It takes an optional HTTP client, like the Tavily adapter.
- **Model name passes through unchanged.** The adapter sends exactly the model name the core service read from Platform Settings. It holds no model names of its own.
- **Thinking:** the port's `thinking` flag becomes OpenRouter's `reasoning: {enabled: true|false}`. The reasoning text is read from the reply message's `reasoning` field and returned as `ModelAnswer.reasoning`, as today. A model that can't think does the closest it can, as the port already says.
- **Tool calls:** the existing tool loop's behaviour is kept: at most 4 rounds, a call with arguments that aren't valid JSON goes back as an error, then a final call with tools turned off. Tools use the OpenAI function format already used. When a Claude model thinks while calling tools, the assistant message sent back each round keeps the reasoning details OpenRouter returned, because Anthropic requires them for the next round.
- **Photos:** sent as an image data URL in a user message, as the DeepSeek adapter does today.
- **Prompt caching (Claude models only):** the system instructions carry a `cache_control` marker. The adapter reads the cached-token count from the reply's usage, and logs it, so caching can be checked.
- **No fallback to OpenRouter credits:** in the OpenRouter account, each BYOK key's "Shared capacity fallback" is set to "Never use any other provider or key for this key's models". That's a manual account step, recorded in the issue and `README`/ops notes. OpenRouter's own docs say this setting is the guarantee.
- **Adapter choice:** `CHAT_MODEL_ADAPTER` gains `openrouter` and it becomes the default. `deepseek` stays as the backup. `OPENROUTER_API_KEY` is added to settings.
- **Direct DeepSeek backup:** when `CHAT_MODEL_ADAPTER=deepseek`, the DeepSeek adapter turns an OpenRouter DeepSeek name into its direct DeepSeek name, so the migrated settings still work. A non-DeepSeek model under this adapter fails with a clear error.
- **Model names migration:** an Alembic data migration renames the saved DeepSeek model names to their OpenRouter names in every `*_model` Platform Setting, in `available_models` and in `model_prices` keys. Admins' own choices are kept, only renamed. The seed file gets the same names. The exact OpenRouter name for `deepseek-flash` and `deepseek-v4-pro` comes from OpenRouter's model list when the issue is worked on.
- **Judge settings:** the eval judge model name gets the same rename. Judge settings are kept apart from Platform Settings (ADR 0015).
- **Available models:** the seed adds at least one Claude model to `available_models`, so Admins can pick it. Every service stays on DeepSeek after this work. Moving a service to Claude is an Admin choice made later.
- **Model Prices:** prices for the Claude models added are set in the seed, in SGD per million tokens, like the DeepSeek ones.
- **Platform Settings are read per call** today, so an Admin's change already reaches the next call. This work must keep that and prove it in the running app.
- **ADR:** add an ADR "Model calls go through OpenRouter, direct DeepSeek kept as backup", updating the adapter list in ADR 0003. Update the Model Price entry in `CONTEXT.md`, which says the estimate uses DeepSeek's prices.

## Testing Decisions

- Good tests check what goes over the wire and what comes back through the port, not the adapter's insides.
- **OpenRouter adapter**, tested through `ChatModel.generate` and `PhotoViewer.look` with `httpx.MockTransport` fake replies. Prior art: the Tavily adapter tests and the DeepSeek adapter tests. Cases:
  - the model name sent is the one given;
  - thinking on/off maps to `reasoning`;
  - reasoning text is returned;
  - tokens are summed across tool rounds;
  - tool calls run and results go back;
  - broken tool-call JSON goes back as an error;
  - the last round is forced to have no tools;
  - reasoning details are kept on the assistant message for the next round;
  - photos are sent as data URLs;
  - Claude models get `cache_control` and DeepSeek models don't;
  - an HTTP error comes back as it does today.
- **Adapter choice:** `openrouter` builds the OpenRouter adapters and `deepseek` still builds the direct ones. Prior art: the load-test adapter-choices tests.
- **DeepSeek backup:** OpenRouter DeepSeek names are mapped to their direct names, and a Claude name fails clearly.
- **Migration:** renames saved names, keeps an Admin's own choice, and renames price keys. Prior art: earlier Platform Settings migration tests.
- **Saving settings:** a name not in `available_models` is refused (existing behaviour, test added if missing).
- **Contract tests** (marked `contract`, real OpenRouter, a few cents): a DeepSeek reply; a Claude reply with thinking and reasoning text; a tool call; a photo; and a repeated Claude call that shows cached tokens.
- **Running-app check (`/run`):** an Admin changes a core service's model in Prompts and models, a message is sent, and the Model Call Log and the OpenRouter activity page both show the new model. Then the same with thinking on, where the reasoning shows in the Model Call Log.

## Out of Scope

- Moving any core service to a Claude model. Admins do that later.
- Using OpenRouter's reported cost in place of Model Prices.
- Automatic switching to direct DeepSeek when OpenRouter fails. The switch is a manual setting.
- Other providers beyond DeepSeek and Anthropic. They should just work by adding names, but aren't tested here.
- Embeddings (local fastembed) and web search (Tavily). They don't use the model adapter.

## Further Notes

- BYOK fee: 5% of list price after the first $25,000 of list-price usage a month on the standard plan, per OpenRouter's BYOK and pricing pages. One third-party guide mentions a change in August 2026 that we couldn't confirm. The operator checks the pricing page once.
- Bug reports in other libraries show `cache_control` being silently dropped on the OpenAI-format path. Plain HTTP avoids that, but the contract test must still show cached tokens.
- Real Users are on the platform: the migration must keep User data and Admin choices, and the switch must be checked in the running app before merge.
- Contract test runs cost a little money. Remind the operator before running them.

## Comments
