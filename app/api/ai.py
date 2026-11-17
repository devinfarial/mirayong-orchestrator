
from anthropic import APIError
from fastapi import APIRouter, HTTPException, status

from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai_service import ai_service


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post(
    "/chat",
    response_model=AIChatResponse
)
async def chat(request: AIChatRequest):

    try:
        response = await ai_service.generate_response(
            request.prompt
        )

        return AIChatResponse(
            response=response,
            model="Claude"
        )

    
    except APIError as e:
        print(f"Anthropic API Error: {type(e).__name__}")
        print(f"Error details: {e}")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": type(e).__name__,
                "message": str(e)
            }
        )