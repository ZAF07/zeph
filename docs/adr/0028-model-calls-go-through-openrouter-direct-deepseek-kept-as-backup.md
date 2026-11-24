# Model calls go through OpenRouter, direct DeepSeek kept as backup

Status: accepted. Built in part (openrouter issues 02 and 03): replies, with tool calls, go through OpenRouter when `CHAT_MODEL_ADAPTER=openrouter`. Photos and making OpenRouter the default come in issue 04. Amends ADR-0003's adapter list.

Every model call went straight to DeepSeek, so trying another provider meant a new adapter per provider. Model calls now go through one OpenRouter adapter behind the `ChatModel` and `PhotoViewer` ports, using the operator's own provider keys (BYOK). A new model is then just a new name in Platform Settings. The adapter is plain `httpx` against OpenRouter's Chat Completions API, not LangChain, so we control the request (`reasoning`, `cache_control`, provider routing) and read the reasoning text straight from the reply. It sends the model name exactly as saved, and the thinking switch becomes `reasoning: {enabled: true|false}`.

The direct DeepSeek adapter stays, chosen with `CHAT_MODEL_ADAPTER=deepseek`, as a way out if OpenRouter is down. It turns OpenRouter DeepSeek names into direct ones and refuses other providers' models.

## Considered Options

- **One adapter per provider (DeepSeek, Anthropic, …).** Rejected: each new provider is new code, tests and keys to wire.
- **LangChain's OpenAI-format client pointed at OpenRouter.** Rejected: it drops the `reasoning` field and is reported to drop `cache_control` silently.
- **Automatic fallback to direct DeepSeek when OpenRouter fails.** Rejected for now: the switch is a manual setting.

## Consequences

- Calls must never spend OpenRouter credits. On each BYOK key in the OpenRouter account, "Shared capacity fallback" is set to "Never use any other provider or key for this key's models" (a manual step; see `docs/DEPLOYMENT_GUIDE.md`).
- `OPENROUTER_API_KEY` is read through config. Choosing `openrouter` without it fails at startup.
- Model Prices are still set by Admins per model name; OpenRouter's reported cost is not used.
