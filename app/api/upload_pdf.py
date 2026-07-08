from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    UploadFile,
)

from app.schemas.response import (
    ApiResponse,
)
from app.services.pdf_pipeline import (
    pdf_pipeline,
)


router = APIRouter(
    tags=["PDF Upload"],
)


@router.post(
    "/upload-pdf",
    response_model=ApiResponse,
)
async def upload_pdf(
    file: UploadFile = File(...),
) -> ApiResponse:

    temp_path = Path(
        f"temp_{file.filename}"
    )

    with open(
        temp_path,
        "wb",
    ) as f:
        f.write(
            await file.read()
        )

    ingested_chunks = (
        pdf_pipeline.ingest_pdf(
            pdf_path=temp_path,
            source_name=file.filename,
        )
    )

    temp_path.unlink(
        missing_ok=True
    )

    return ApiResponse(
        success=True,
        message=(
            "PDF uploaded successfully"
        ),
        data={
            "filename": file.filename,
            "chunks_ingested": (
                ingested_chunks
            ),
        },
    )