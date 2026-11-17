import copy
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.repositories.episode_repository import EpisodeRepository
from app.schemas.script import EpisodeScript
from app.services import script_service
from app.services.script_service import (
    ScriptGenerationError,
    ScriptNotAllowedError,
    ScriptService,
    extract_json,
)

VALID_SCRIPT = {
    "title": "Meet the Color Red",
    "learning_objective": "Recognize and name the color red.",
    "target_age_band": "4-6",
    "hook": "Can you spot something red?",
    "scenes": [
        {
            "sequence_number": i,
            "narration_text": f"Red scene number {i}.",
            "visual_prompt": "A friendly round fox in a sunny meadow, colorful 3D animation",
            "duration_seconds": 8,
            "on_screen_text": "Red" if i == 1 else None,
        }
        for i in (1, 2, 3)
    ],
    "closing_recap": "Red is the color of apples and fire trucks!",
}


class FakeAI:
    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []

    async def generate_response(self, prompt, system=None, max_tokens=1024):
        self.prompts.append(prompt)
        return self.replies.pop(0)


@pytest.fixture
def fake_repo(monkeypatch):
    episode = SimpleNamespace(
        id=1,
        title="Red",
        topic="The color red",
        target_age_band="4-6",
        description=None,
        status="draft",
        script_json=None,
    )
    saved = {}

    async def get_by_id(db, episode_id):
        return episode if episode_id == 1 else None

    async def save_script(db, ep, script):
        ep.script_json = script
        ep.status = "script_ready"
        saved["script"] = script
        return ep

    monkeypatch.setattr(EpisodeRepository, "get_by_id", get_by_id)
    monkeypatch.setattr(EpisodeRepository, "save_script", save_script)
    return episode, saved


def to_json(script):
    import json
    return json.dumps(script)


def test_extract_json_handles_code_fences():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_extract_json_handles_surrounding_prose():
    assert extract_json('Here you go: {"a": 1} Enjoy!') == {"a": 1}


def test_extract_json_rejects_non_json():
    with pytest.raises(ValueError):
        extract_json("sorry, I can't do that")


def test_valid_script_passes():
    script = EpisodeScript.model_validate(VALID_SCRIPT)
    assert script.total_duration_seconds == 24


def test_too_long_script_rejected():
    data = copy.deepcopy(VALID_SCRIPT)
    for scene in data["scenes"]:
        scene["duration_seconds"] = 14  # 42s total
    with pytest.raises(ValidationError):
        EpisodeScript.model_validate(data)


def test_too_few_scenes_rejected():
    data = copy.deepcopy(VALID_SCRIPT)
    data["scenes"] = data["scenes"][:2]
    with pytest.raises(ValidationError):
        EpisodeScript.model_validate(data)


def test_out_of_order_scenes_rejected():
    data = copy.deepcopy(VALID_SCRIPT)
    data["scenes"][0]["sequence_number"] = 5
    with pytest.raises(ValidationError):
        EpisodeScript.model_validate(data)


@pytest.mark.asyncio
async def test_generate_script_saves_valid_reply(fake_repo):
    episode, saved = fake_repo
    ai = FakeAI([to_json(VALID_SCRIPT)])

    result = await ScriptService.generate_script(None, 1, ai=ai)

    assert result.status == "script_ready"
    assert saved["script"]["title"] == "Meet the Color Red"
    assert len(ai.prompts) == 1


@pytest.mark.asyncio
async def test_generate_script_retries_once_with_error_feedback(fake_repo):
    ai = FakeAI(["not json at all", to_json(VALID_SCRIPT)])

    result = await ScriptService.generate_script(None, 1, ai=ai)

    assert result.status == "script_ready"
    assert len(ai.prompts) == 2
    assert "rejected" in ai.prompts[1]


@pytest.mark.asyncio
async def test_generate_script_gives_up_after_max_attempts(
    fake_repo, monkeypatch
):
    monkeypatch.setattr(script_service.settings, "SCRIPT_MAX_ATTEMPTS", 2)
    episode, saved = fake_repo
    ai = FakeAI(["bad", "still bad", to_json(VALID_SCRIPT)])

    with pytest.raises(ScriptGenerationError):
        await ScriptService.generate_script(None, 1, ai=ai)

    assert len(ai.prompts) == 2  # bounded: third reply never requested
    assert "script" not in saved
    assert episode.status == "draft"


@pytest.mark.asyncio
async def test_generate_script_unknown_episode_returns_none(fake_repo):
    assert await ScriptService.generate_script(None, 99, ai=FakeAI([])) is None


@pytest.mark.asyncio
async def test_generate_script_blocked_for_later_states(fake_repo):
    episode, _ = fake_repo
    episode.status = "rendered"
    ai = FakeAI([to_json(VALID_SCRIPT)])

    with pytest.raises(ScriptNotAllowedError):
        await ScriptService.generate_script(None, 1, ai=ai)

    assert ai.prompts == []  # no paid call was made
