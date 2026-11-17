from enum import StrEnum

class EpisodeStatus(StrEnum):
    DRAFT = "draft"
    SCRIPT_READY = "script_ready"
    ASSETS_GENERATED = "assets_generated"
    RENDERED = "rendered"
    VALIDATED = "validated"
    PUBLISH_QUEUED = "publish_queued"
    PUBLISHED = "published"
    FAILED = "failed"

class InvalidStateTransitionError(Exception):
    """Raised when an episode attempts an illegal state transition."""

ALLOWED_TRANSITIONS: dict[EpisodeStatus, set[EpisodeStatus]] = {
    EpisodeStatus.DRAFT: {
        EpisodeStatus.SCRIPT_READY,
        EpisodeStatus.FAILED,
    },
    EpisodeStatus.SCRIPT_READY: {
        EpisodeStatus.SCRIPT_READY,
        EpisodeStatus.ASSETS_GENERATED,
        EpisodeStatus.FAILED,
    },
    EpisodeStatus.ASSETS_GENERATED: {
        EpisodeStatus.RENDERED,
        EpisodeStatus.FAILED,
    },
    EpisodeStatus.RENDERED: {
        EpisodeStatus.VALIDATED,
        EpisodeStatus.FAILED,
    },
    EpisodeStatus.VALIDATED: {
        EpisodeStatus.PUBLISH_QUEUED,
        EpisodeStatus.FAILED,
    },
    EpisodeStatus.PUBLISH_QUEUED: {
        EpisodeStatus.PUBLISHED,
        EpisodeStatus.FAILED,
    },
    EpisodeStatus.PUBLISHED: set(),
    EpisodeStatus.FAILED: {
        EpisodeStatus.DRAFT,
        EpisodeStatus.SCRIPT_READY,
        EpisodeStatus.ASSETS_GENERATED,
        EpisodeStatus.RENDERED,
        EpisodeStatus.VALIDATED,
        EpisodeStatus.PUBLISH_QUEUED,
    },
}

def can_transition(
    current: str | EpisodeStatus,
    target: str | EpisodeStatus,
) -> bool:
    """Return True if moving from current -> target is allowed."""
    try:
        current_status = EpisodeStatus(current)
        target_status = EpisodeStatus(target)
    except ValueError:
        return False
    return target_status in ALLOWED_TRANSITIONS.get(current_status, set())

def validate_transition(
    current: str | EpisodeStatus,
    target: str | EpisodeStatus,
) -> EpisodeStatus:
    """Validate current -> target transition and return target as EpisodeStatus."""
    try:
        current_status = EpisodeStatus(current)
    except ValueError as e:
        raise InvalidStateTransitionError(
            f"Unknown current status: '{current}'"
        ) from e
    try:
        target_status = EpisodeStatus(target)
    except ValueError as e:
        raise InvalidStateTransitionError(
            f"Unknown target status: '{target}'"
        ) from e
    if not can_transition(current_status, target_status):
        raise InvalidStateTransitionError(
            f"Cannot transition episode from '{current_status}' to '{target_status}'"
        )
    return target_status