
from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    prompt: str = Field(min_length=1)


class AIChatResponse(BaseModel):
    response: str
    model: str
