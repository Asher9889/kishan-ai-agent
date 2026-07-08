from fastapi import APIRouter, File, UploadFile, HTTPException

from app.schemas.response import ApiResponse
from app.services.speech_pipeline import speech_pipeline


router = APIRouter(tags=["Speech"])


@router.post(
    "/transcribe",
    response_model=ApiResponse,
)
async def transcribe_audio(
    file: UploadFile = File(...),
) -> ApiResponse:

    try:
        # ==========================================
        # READ AUDIO FILE AS BYTES
        # ==========================================
        audio_bytes = await file.read()

        # ==========================================
        # VALIDATE EMPTY FILE
        # ==========================================
        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="Empty audio file uploaded"
            )

        # ==========================================
        # PROCESS AUDIO
        # ==========================================
        result = await speech_pipeline.process(
            audio_bytes
        )

        # ==========================================
        # SUCCESS RESPONSE
        # ==========================================
        return ApiResponse(
            success=True,
            message="Transcription completed successfully",
            data=result,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )
