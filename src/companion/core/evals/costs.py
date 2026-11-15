from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from companion.core.errors import InvalidError
from companion.core.evals.models import Cost, EvalName, ModelTokens
from companion.core.models import User
from companion.core.platform_settings import (
    AVAILABLE_MODELS,
    EVAL_RUN_TOKEN_LIMIT,
    MODEL_PRICES,
    ModelPrice,
    read_model_prices,
)
from companion.core.ports import Clock, PlatformSettingsRepository

TOKENS_PER_PRICE = 1_000_000
LOWEST_TOKEN_LIMIT = 10_000
HIGHEST_TOKEN_LIMIT = 50_000_000
HIGHEST_PRICE_SGD = 1_000.0

ROUGH_TOKENS_PER_CASE: dict[EvalName, ModelTokens] = {
    EvalName.SAFEGUARD: ModelTokens(4_000, 400),
    EvalName.PERSONA: ModelTokens(9_000, 900),
    EvalName.KNOWLEDGE: ModelTokens(20_000, 1_500),
    EvalName.SETTINGS: ModelTokens(4_500, 400),
    EvalName.PHOTO_DESCRIPTIONS: ModelTokens(1_500, 200),
    EvalName.UNDERSTANDING: ModelTokens(12_000, 1_500),
}


def stored_prices(settings: Mapping[str, Any]) -> dict[str, ModelPrice]:
    """Read the Model Prices from some settings, such as a run's snapshot.

    Args:
        settings: Platform Settings by key.

    Returns:
        Each priced model's price; none if the settings have no prices.
    """
    if MODEL_PRICES.key not in settings:
        return {}
    return read_model_prices(settings[MODEL_PRICES.key])


def price_tokens(
    tokens_by_model: Mapping[str, ModelTokens], prices: Mapping[str, ModelPrice]
) -> Cost:
    """Price some tokens in SGD.

    A model with no price never blocks anything: its tokens are left out
    of the SGD and it is named instead.

    Args:
        tokens_by_model: The tokens, by the model that used them.
        prices: Each priced model's price.

    Returns:
        The cost, and the models with tokens but no price.
    """
    sgd = 0.0
    unpriced = []
    for model, tokens in sorted(tokens_by_model.items()):
        price = prices.get(model)
        if price is None:
            if tokens.tokens_in or tokens.tokens_out:
                unpriced.append(model)
            continue
        sgd += (
            tokens.tokens_in * price.sgd_in + tokens.tokens_out * price.sgd_out
        ) / TOKENS_PER_PRICE
    return Cost(sgd=sgd, unpriced_models=unpriced)


@dataclass(frozen=True)
class EvalCosts:
    """What keeps Eval Runs' cost in check.

    Attributes:
        prices: One row per model Admins can pick or that has a price; a
            model without a price has None for both.
        token_limit: The most tokens one Eval Run may use.
    """

    prices: list[tuple[str, ModelPrice | None]]
    token_limit: int


class InvalidEvalCostsError(InvalidError):
    """Raised when a Model Price or the token limit isn't allowed."""


class EvalCostsService:
    """Lets Admins read and change the Model Prices and the token limit.

    Both are Platform Settings (ADR-0004), saved the way the settings pages
    save theirs.
    """

    def __init__(self, settings: PlatformSettingsRepository, clock: Clock) -> None:
        """Set up the service.

        Args:
            settings: Where Platform Settings are stored.
            clock: Tells the time.
        """
        self._settings = settings
        self._clock = clock

    def get(self) -> EvalCosts:
        """Read the Model Prices and the token limit.

        Returns:
            A row for every model Admins can pick, then any other priced
            model, and the limit.
        """
        settings = self._settings.load()
        prices = settings.get(MODEL_PRICES)
        models = list(dict.fromkeys([*settings.get(AVAILABLE_MODELS), *prices]))
        return EvalCosts(
            prices=[(model, prices.get(model)) for model in models],
            token_limit=settings.get(EVAL_RUN_TOKEN_LIMIT),
        )

    def update(
        self, admin: User, prices: Sequence[ModelPrice], token_limit: int
    ) -> EvalCosts:
        """Check and save the Model Prices and the token limit together.

        Models left out of `prices` have no price afterwards.

        Args:
            admin: The Admin saving them.
            prices: Every model's price.
            token_limit: The most tokens one Eval Run may use.

        Returns:
            The prices and limit after saving.

        Raises:
            InvalidEvalCostsError: If a price or the limit is out of range,
                or a model is named twice; nothing is saved.
        """
        if not LOWEST_TOKEN_LIMIT <= token_limit <= HIGHEST_TOKEN_LIMIT:
            raise InvalidEvalCostsError(
                f"The token limit must be from {LOWEST_TOKEN_LIMIT:,} "
                f"to {HIGHEST_TOKEN_LIMIT:,}."
            )
        stored: dict[str, dict[str, float]] = {}
        for price in prices:
            model = price.model.strip()
            if not model:
                raise InvalidEvalCostsError("Every price needs a model name.")
            if model in stored:
                raise InvalidEvalCostsError(f"{model} has two prices.")
            for amount in (price.sgd_in, price.sgd_out):
                if not 0 <= amount <= HIGHEST_PRICE_SGD:
                    raise InvalidEvalCostsError(
                        f"{model}'s prices must be from 0 to {HIGHEST_PRICE_SGD:,.0f} "
                        "SGD per 1M tokens."
                    )
            stored[model] = {"in": price.sgd_in, "out": price.sgd_out}
        self._settings.save_many(
            {MODEL_PRICES.key: stored, EVAL_RUN_TOKEN_LIMIT.key: token_limit},
            self._clock.now(),
            admin.id,
        )
        return self.get()
