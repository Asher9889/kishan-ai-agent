from fastapi import APIRouter, Request, File, UploadFile, HTTPException
from app.ai.whisper_service import get_whisper_service
from app.schemas.response import ApiResponse
from app.services.speech_pipeline import speech_pipeline
from array import array


router = APIRouter(tags=["Speech"])


@router.post("/transcribe", response_model=ApiResponse)
async def transcribe_audio(file: UploadFile = File(...)) -> ApiResponse:
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




@router.post("/transcribe-pcm", response_model=ApiResponse)
async def transcribe_pcm(request: Request) -> ApiResponse:
    try:
        # ==========================================
        # READ RAW PCM BYTES
        # ==========================================
        pcm_bytes = await request.body()

        if not pcm_bytes:
            raise HTTPException(
                status_code=400,
                detail="Empty PCM buffer received",
            )

        # ==========================================
        # SAMPLE RATE HEADER
        # ==========================================
        sample_rate = int(
            request.headers.get(
                "X-Sample-Rate",
                "48000",
            )
        )

        # ==========================================
        # CONVERT BYTES -> INT16 PCM
        # ==========================================
        pcm_buffer = array("h")
        pcm_buffer.frombytes(pcm_bytes)

        # ==========================================
        # TRANSCRIBE
        # ==========================================
        whisper = get_whisper_service()

        result = whisper.transcribe_pcm(
            pcm_buffer=pcm_buffer,
            sample_rate=sample_rate,
        )
        
        return ApiResponse(
            success=True,
            message="PCM transcription completed successfully",
            data=result,
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PCM transcription failed: {e}",
        )