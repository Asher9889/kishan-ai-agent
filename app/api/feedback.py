from datetime import datetime

from fastapi import APIRouter

from app.core.logger import logger
from app.schemas.feedback import FeedbackRequest
from app.schemas.response import ApiResponse
from app.services.feedback_service import feedback_service


router = APIRouter(tags=["Feedback"])


@router.post(
    "/feedback",
    response_model=ApiResponse,
)
async def submit_feedback(
    request: FeedbackRequest,
) -> ApiResponse:
    # 1. Build feedback record for API response
    feedback_record = {
        "query": request.query,
        "answer": request.answer,
        "feedback": request.feedback,
        "comments": request.comments,
        "confidence": request.confidence,
        "source_document_id": (
            request.source_document_id
        ),
        "timestamp": datetime.utcnow().isoformat(),
    }

    # 2. Log feedback
    logger.info(
        "Feedback received",
        feedback=request.feedback,
        source_document_id=(
            request.source_document_id
        ),
    )

    # 3. Save feedback to MSSQL
    feedback_service.save(request)

    # 4. Return API response
    return ApiResponse(
        success=True,
        message="Feedback recorded successfully",
        data=feedback_record,
    )