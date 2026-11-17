
from anthropic import AsyncAnthropic
from google import genai

from app.core.config import settings
import time



class AIService:

    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()

        self.anthropic_client = None
        self.gemini_client = None

        if self.provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is not configured")

            self.anthropic_client = AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )

        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is not configured")

            self.gemini_client = genai.Client(
                api_key=settings.GEMINI_API_KEY
            )

        else:
            raise ValueError(
                f"Unsupported AI provider: {self.provider}"
            )

    async def generate_response(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024
    ) -> str:

        if self.provider == "anthropic":
            return await self._generate_anthropic(prompt, system, max_tokens)

        if system:
            prompt = f"{system}\n\n---\n\n{prompt}"

        return await self._generate_gemini(prompt)

    async def _generate_anthropic(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int
    ) -> str:

        kwargs = {"system": system} if system else {}

        response = await self.anthropic_client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            **kwargs,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return "".join(
            block.text
            for block in response.content
            if block.type == "text"
        )

    
    import time

    async def _generate_gemini(self, prompt: str) -> str:

        start = time.perf_counter()

        print("Sending request to Gemini...")

        interaction = await self.gemini_client.aio.interactions.create(
            model=settings.GEMINI_MODEL,
            input=prompt
        )

        elapsed = time.perf_counter() - start

        print(f"Gemini response received in {elapsed:.2f} seconds")

        return interaction.output_text or ""


    async def close(self):

        if self.anthropic_client:
            await self.anthropic_client.close()

        if self.gemini_client:
            await self.gemini_client.aio.aclose()


ai_service = AIService()