from pathlib import Path
from uuid import uuid4

import pandas as pd
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.schemas.response import ApiResponse
from app.services.ingestion_pipeline import (
    ingestion_pipeline,
)


router = APIRouter(
    tags=["CSV Upload"],
)


@router.post(
    "/upload-csv",
    response_model=ApiResponse,
)
async def upload_csv(
    file: UploadFile = File(...),
) -> ApiResponse:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file uploaded",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension != ".csv":
        raise HTTPException(
            status_code=400,
            detail="Only CSV files allowed",
        )

    try:
        contents = await file.read()

        df = pd.read_csv(
            pd.io.common.BytesIO(contents)
        )

        ingested_count = 0

        for row in df.to_dict(
            orient="records"
        ):
            ingestion_pipeline.ingest(
                record=row,
                document_id=str(uuid4()),
            )

            ingested_count += 1

        return ApiResponse(
            success=True,
            message=(
                "CSV uploaded successfully"
            ),
            data={
                "filename": file.filename,
                "rows_ingested": (
                    ingested_count
                ),
            },
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc