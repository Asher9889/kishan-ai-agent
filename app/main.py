import sys
import os
from contextlib import asynccontextmanager


os.environ["PYTHONIOENCODING"] = "utf-8"

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.speech import router as speech_router
from app.core.config import settings
from app.core.logger import logger
from app.api.query import router as query_router
from app.api.ask import router as ask_router
from app.api.ask_audio import router as ask_audio_router
from app.api.feedback import (
    router as feedback_router
)
from app.api.knowledge import (
    router as knowledge_router,
)
from app.api.upload_csv import (
    router as upload_csv_router,
)
from app.api.upload_pdf import (
    router as pdf_router,
)
from app.api.ask_stream import (
    router as ask_stream_router
)
from app.api.quick_knowledge import (
    router as quick_knowledge_router,
)
from app.api.ask_v3 import (
    router as ask_v3_router
)
from app.api.ask_image import (
    router as ask_image_router
)

from app.services.image_pipeline import (
    image_pipeline
)
from app.api.ask_image_followup import (
    router as ask_image_followup_router,
)

from app.livekit_agent.runner import (
    start_livekit_process
)


livekit_process=None

@asynccontextmanager
async def lifespan(app: FastAPI):

    global livekit_process

    print("Starting LiveKit Agent...")
    livekit_process = (start_livekit_process())

    yield


    if livekit_process:
        livekit_process.terminate()



app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered Farmer Knowledge System",
    lifespan=lifespan
)



app.include_router(health_router)
app.include_router(speech_router)
app.include_router(query_router)
app.include_router(ask_router)
app.include_router(ask_audio_router)
app.include_router(feedback_router)
app.include_router(knowledge_router)
app.include_router(upload_csv_router)
app.include_router(pdf_router)
app.include_router(ask_stream_router)
app.include_router(quick_knowledge_router)
app.include_router(ask_v3_router)
app.include_router(ask_image_router)
app.include_router(ask_image_followup_router)

@app.on_event("startup")
async def startup_event() -> None:

    logger.info("KrishiGPT server started", app_name=settings.APP_NAME)

    try:
        logger.info("Loading Qwen Vision Model...")

        image_pipeline.load_models()

        logger.info("Qwen Vision Model Loaded Successfully")

    except Exception as exc:

        logger.exception("Failed to load Qwen Vision Model", error=str(exc))

        raise

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error", path=str(request.url.path), error=str(exc))

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "data": None,
        },
    )


@app.get("/")
async def root() -> dict[str, str]:
    logger.info("Root endpoint called")

    return {
        "message": f"{settings.APP_NAME} API Running"
    }