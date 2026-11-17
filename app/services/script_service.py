import json
import re
from functools import lru_cache
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.episode import Episode
from app.repositories.episode_repository import EpisodeRepository
from app.schemas.script import EpisodeScript
from app.services.ai_service import AIService, ai_service

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "script_writer.md"

# Statuses from which a script may be (re)generated.
SCRIPT_ALLOWED_STATUSES = {"draft", "script_ready"}


class ScriptGenerationError(Exception):
    """The model did not return a valid script within the allowed attempts."""


class ScriptNotAllowedError(Exception):
    """The episode is in a state where its script can't be generated."""


@lru_cache
def load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def extract_json(text: str) -> dict:
    """Pull a JSON object out of a model reply, tolerating code fences."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)

    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in model reply")

    return json.loads(text[start:end + 1])


def build_user_prompt(episode: Episode) -> str:
    lines = [
        f"Topic: {episode.topic or episode.title}",
        f"Working title: {episode.title}",
        f"Target age band: {episode.target_age_band or settings.DEFAULT_TARGET_AGE_BAND}",
        f"Language: {episode.language or settings.DEFAULT_LANGUAGE}",
    ]
    if episode.description:
        lines.append(f"Notes from the producer: {episode.description}")

    return "\n".join(lines)


class ScriptService:

    @staticmethod
    async def generate_script(
        db: AsyncSession,
        episode_id: int,
        ai: AIService = ai_service
    ) -> Episode | None:
        episode = await EpisodeRepository.get_by_id(db, episode_id)

        if episode is None:
            return None

        if episode.status not in SCRIPT_ALLOWED_STATUSES:
            raise ScriptNotAllowedError(
                f"Cannot generate a script for an episode in "
                f"'{episode.status}' status"
            )

        base_prompt = build_user_prompt(episode)
        prompt = base_prompt
        last_error = "unknown error"

        # Every attempt is a paid call, so the loop is strictly bounded.
        for _ in range(settings.SCRIPT_MAX_ATTEMPTS):
            reply = await ai.generate_response(
                prompt,
                system=load_system_prompt(),
                max_tokens=settings.SCRIPT_MAX_TOKENS
            )

            try:
                script = EpisodeScript.model_validate(extract_json(reply))
            except (ValueError, ValidationError) as e:
                last_error = str(e)
                prompt = (
                    f"{base_prompt}\n\nYour previous reply was rejected:\n"
                    f"{last_error}\n\nReturn a corrected JSON object only."
                )
                continue

            return await EpisodeRepository.save_script(
                db, episode, script.model_dump(mode="json")
            )

        raise ScriptGenerationError(
            f"No valid script after {settings.SCRIPT_MAX_ATTEMPTS} "
            f"attempts. Last error: {last_error}"
        )
