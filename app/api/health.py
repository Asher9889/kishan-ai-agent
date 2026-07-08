from fastapi import APIRouter

from app.schemas.response import ApiResponse


router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=ApiResponse,
)
async def health_check() -> ApiResponse:
    return ApiResponse(
        success=True,
        message="Service is healthy",
        data={
            "status": "ok",
        },
    )