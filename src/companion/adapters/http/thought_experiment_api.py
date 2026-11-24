from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from companion.core.models import (
    CuriositySensitivity,
    ThoughtExperiment,
    ThoughtExperimentDetails,
    User,
)
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.thought_experiments import ThoughtExperimentService


class ThoughtExperimentResponse(BaseModel):
    """A Thought Experiment as Admins see it, with how often it was asked."""

    id: str
    wording: str
    pattern_type_id: str
    other_pattern_type_id: str
    sensitivity: CuriositySensitivity
    starter: bool
    on: bool
    archived_at: datetime | None
    asked_count: int


class PatternTypeChoiceResponse(BaseModel):
    """A Pattern Type a Thought Experiment can name."""

    id: str
    name: str


class ThoughtExperimentsResponse(BaseModel):
    """Every Thought Experiment, oldest first, and the Pattern Types to pick from."""

    thought_experiments: list[ThoughtExperimentResponse]
    pattern_types: list[PatternTypeChoiceResponse]


class ThoughtExperimentRequest(BaseModel):
    """What an Admin sets on a Thought Experiment.

    `save_anyway` saves it even when its wording may lead to an answer.
    """

    wording: str
    pattern_type_id: str
    other_pattern_type_id: str
    sensitivity: CuriositySensitivity
    starter: bool = False
    on: bool = True
    save_anyway: bool = False

    def to_details(self) -> ThoughtExperimentDetails:
        """Turn the request into Thought Experiment details.

        Returns:
            The details.
        """
        return ThoughtExperimentDetails(
            wording=self.wording,
            pattern_type_id=self.pattern_type_id,
            other_pattern_type_id=self.other_pattern_type_id,
            sensitivity=self.sensitivity,
            starter=self.starter,
            on=self.on,
        )


def to_thought_experiment_response(
    thought_experiment: ThoughtExperiment, asked_count: int
) -> ThoughtExperimentResponse:
    """Turn a Thought Experiment into its API response.

    Args:
        thought_experiment: The Thought Experiment.
        asked_count: How many times it was put to a User.

    Returns:
        The response.
    """
    details = thought_experiment.details
    return ThoughtExperimentResponse(
        id=str(thought_experiment.id),
        wording=details.wording,
        pattern_type_id=details.pattern_type_id,
        other_pattern_type_id=details.other_pattern_type_id,
        sensitivity=details.sensitivity,
        starter=details.starter,
        on=details.on,
        archived_at=thought_experiment.archived_at,
        asked_count=asked_count,
    )


def build_thought_experiment_api_router(
    current_admin: Callable[..., User],
    thought_experiment_service: ThoughtExperimentService,
    pattern_catalog_service: PatternCatalogService,
) -> APIRouter:
    """Build the routes Admins manage Thought Experiments with.

    There is no route that deletes one: they are archived instead.

    Args:
        current_admin: The dependency that lets only Admins through.
        thought_experiment_service: Manages Thought Experiments.
        pattern_catalog_service: Reads the Pattern Types to pick from.

    Returns:
        The router.
    """
    router = APIRouter(prefix="/api/admin", dependencies=[Depends(current_admin)])

    def respond(thought_experiment: ThoughtExperiment) -> ThoughtExperimentResponse:
        """Answer with one Thought Experiment and how often it was asked.

        Args:
            thought_experiment: The Thought Experiment.

        Returns:
            The response.
        """
        return to_thought_experiment_response(
            thought_experiment,
            thought_experiment_service.asked_counts().get(thought_experiment.id, 0),
        )

    @router.get("/thought-experiments")
    def list_thought_experiments() -> ThoughtExperimentsResponse:
        """List every Thought Experiment and the Pattern Types to pick from.

        Returns:
            The Thought Experiments, oldest first, archived ones included,
            and the catalog's Pattern Types by ID.
        """
        asked_counts = thought_experiment_service.asked_counts()
        return ThoughtExperimentsResponse(
            thought_experiments=[
                to_thought_experiment_response(
                    thought_experiment, asked_counts.get(thought_experiment.id, 0)
                )
                for thought_experiment in thought_experiment_service.list_all()
            ],
            pattern_types=sorted(
                (
                    PatternTypeChoiceResponse(
                        id=entry.pattern_type.id, name=entry.pattern_type.name
                    )
                    for entry in pattern_catalog_service.catalog()
                ),
                key=lambda choice: choice.id,
            ),
        )

    @router.post("/thought-experiments", status_code=status.HTTP_201_CREATED)
    def add_thought_experiment(
        request: ThoughtExperimentRequest,
    ) -> ThoughtExperimentResponse:
        """Add a Thought Experiment.

        Args:
            request: What the Admin set.

        Returns:
            The saved Thought Experiment.

        Raises:
            CoreError: 422 if a detail isn't valid, or if the wording may
                lead to an answer and `save_anyway` isn't set (`fields`
                then has `leading`, one flag per line).
        """
        return respond(
            thought_experiment_service.add(request.to_details(), request.save_anyway)
        )

    @router.put("/thought-experiments/{thought_experiment_id}")
    def update_thought_experiment(
        thought_experiment_id: UUID, request: ThoughtExperimentRequest
    ) -> ThoughtExperimentResponse:
        """Change a Thought Experiment, or switch it on or off.

        Args:
            thought_experiment_id: The Thought Experiment to change.
            request: Its new values.

        Returns:
            The saved Thought Experiment.

        Raises:
            CoreError: 404 if there is no such one; 409 if it is archived;
                422 as when adding.
        """
        return respond(
            thought_experiment_service.update(
                thought_experiment_id, request.to_details(), request.save_anyway
            )
        )

    @router.post("/thought-experiments/{thought_experiment_id}/archive")
    def archive_thought_experiment(
        thought_experiment_id: UUID,
    ) -> ThoughtExperimentResponse:
        """Archive a Thought Experiment, so it is never asked again.

        Args:
            thought_experiment_id: The Thought Experiment to archive.

        Returns:
            The archived Thought Experiment.

        Raises:
            CoreError: 404 if there is no such one.
        """
        return respond(thought_experiment_service.archive(thought_experiment_id))

    return router
