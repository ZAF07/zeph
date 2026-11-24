# Model calls go through OpenRouter, direct DeepSeek kept as backup

Status: accepted. Built (openrouter issues 02 to 05): replies, tool calls and photos go through OpenRouter, `openrouter` is the default `CHAT_MODEL_ADAPTER`, and Admins can pick two Claude models (`anthropic/claude-haiku-5.5`, `anthropic/claude-sonnet-5.5`) beside the DeepSeek ones. Amends ADR-0003's adapter list.

Every model call went straight to DeepSeek, so trying another provider meant a new adapter per provider. Model calls now go through one OpenRouter adapter behind the `ChatModel` and `PhotoViewer` ports, using the operator's own provider keys (BYOK). A new model is then just a new name in Platform Settings. The adapter is plain `httpx` against OpenRouter's Chat Completions API, not LangChain, so we control the request (`reasoning`, `cache_control`, provider routing) and read the reasoning text straight from the reply. It sends the model name exactly as saved, and the thinking switch becomes `reasoning: {enabled: true|false}`.

The direct DeepSeek adapter stays, chosen with `CHAT_MODEL_ADAPTER=deepseek`, as a way out if OpenRouter is down. It turns OpenRouter DeepSeek names into direct ones and refuses other providers' models.

## Considered Options

- **One adapter per provider (DeepSeek, Anthropic, …).** Rejected: each new provider is new code, tests and keys to wire.
- **LangChain's OpenAI-format client pointed at OpenRouter.** Rejected: it drops the `reasoning` field and is reported to drop `cache_control` silently.
- **Automatic fallback to direct DeepSeek when OpenRouter fails.** Rejected for now: the switch is a manual setting.

## Consequences

- Calls must never spend OpenRouter credits. On each BYOK key in the OpenRouter account, "Shared capacity fallback" is set to "Never use any other provider or key for this key's models", and the account's privacy settings allow providers that may train on inputs, or DeepSeek's own servers are refused (manual steps; see `docs/DEPLOYMENT_GUIDE.md`).
- Each request allows only the model's maker to answer (`provider: {only: [<the part of the name before "/">]}`), because our keys are the makers' keys. Without it, a model its maker does not serve under that name is quietly answered by another host on credits; with it, the call fails. This is why the saved DeepSeek names are the dated ones DeepSeek itself serves. A model whose maker is not also its OpenRouter provider can't be called until this rule is widened.
- The adapter logs a warning when a reply's usage says it was not paid with our own key.
- `OPENROUTER_API_KEY` is read through config. A chosen adapter without its key fails at startup; `DEEPSEEK_API_KEY` is only needed for the `deepseek` backup.
- Model Prices are still set by Admins per model name; OpenRouter's reported cost is not used.
- With thinking on, a Claude model decides for itself whether a call needs thinking. An easy call comes back with no reasoning text, so an empty reasoning in the Model Call Log is not an error.
