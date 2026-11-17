import pytest

from app.core.state_machine import (
    EpisodeStatus,
    InvalidStateTransitionError,
    can_transition,
    validate_transition,
)


def test_happy_path_transitions():
    pipeline = [
        EpisodeStatus.DRAFT,
        EpisodeStatus.SCRIPT_READY,
        EpisodeStatus.ASSETS_GENERATED,
        EpisodeStatus.RENDERED,
        EpisodeStatus.VALIDATED,
        EpisodeStatus.PUBLISH_QUEUED,
        EpisodeStatus.PUBLISHED,
    ]
    for current_state, next_state in zip(pipeline, pipeline[1:]):
        assert can_transition(current_state, next_state) is True
        assert validate_transition(current_state, next_state) == next_state


def test_script_can_be_regenerated_when_script_ready():
    assert can_transition(EpisodeStatus.SCRIPT_READY, EpisodeStatus.SCRIPT_READY) is True


def test_skipping_stages_is_rejected():
    assert can_transition(EpisodeStatus.DRAFT, EpisodeStatus.PUBLISHED) is False
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(EpisodeStatus.DRAFT, EpisodeStatus.PUBLISHED)


def test_published_is_terminal():
    for target in EpisodeStatus:
        assert can_transition(EpisodeStatus.PUBLISHED, target) is False


def test_any_active_stage_can_fail_and_recover():
    assert validate_transition(EpisodeStatus.ASSETS_GENERATED, EpisodeStatus.FAILED) == EpisodeStatus.FAILED
    assert validate_transition(EpisodeStatus.FAILED, EpisodeStatus.ASSETS_GENERATED) == EpisodeStatus.ASSETS_GENERATED


def test_unknown_status_raises_invalid_transition():
    assert can_transition("draft", "not_a_real_state") is False
    with pytest.raises(InvalidStateTransitionError):
        validate_transition("draft", "not_a_real_state")