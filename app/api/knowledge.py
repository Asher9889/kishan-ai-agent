from fastapi import APIRouter

from app.schemas.knowledge import (
    KnowledgeRecord,
)
from app.schemas.response import ApiResponse
from app.services.ingestion_pipeline import (
    ingestion_pipeline,
)


router = APIRouter(
    tags=["Knowledge"],
)


@router.post(
    "/upload-knowledge",
    response_model=ApiResponse,
)
async def upload_knowledge(
    request: KnowledgeRecord,
) -> ApiResponse:
    document_id = (
        ingestion_pipeline.ingest(
            record=request.model_dump(),
        )
    )

    return ApiResponse(
        success=True,
        message="Knowledge uploaded successfully",
        data={
            "document_id": document_id,
            "category": request.category,
            "crop": request.crop,
        },
    )