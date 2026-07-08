import json

from fastapi import (
    APIRouter,
)

from pydantic import BaseModel

from app.ai.llm import (
    llm_service,
)

from app.services.chat_memory_service import (
    chat_memory_service,
)

from app.core.logger import (
    logger,
)

router = APIRouter(
    tags=["Ask Image Followup"]
)


class ImageFollowupRequest(
    BaseModel
):
    thread_id: str
    question: str


@router.post(
    "/ask-image-followup"
)
async def ask_image_followup(
    request: ImageFollowupRequest,
):

    try:

        memory = (
            chat_memory_service
            .get_recent_messages(
                thread_id=request.thread_id,
                limit=50,
            )
        )

        image_context = None

        for item in reversed(memory):

            try:

                msg = item.get(
                    "message",
                    ""
                )

                parsed = json.loads(
                    msg
                )

                if (
                    parsed.get("type")
                    == "image_diagnosis"
                ):

                    image_context = parsed
                    break

            except Exception:
                pass

        if image_context is None:

            return {
                "success": False,
                "error": (
                    "No image diagnosis found "
                    "for this thread."
                ),
            }

        image_analysis = (
            image_context.get(
                "image_analysis",
                {},
            )
        )

        diagnosis = (
            image_context.get(
                "diagnosis",
                {},
            )
        )

        crop_name = (
            image_analysis.get(
                "crop_name",
                "Unknown"
            )
        )

        scientific_name = (
            image_analysis.get(
                "scientific_name",
                ""
            )
        )

        system_prompt = f"""
You are KrishiMitra AI.

You are continuing an existing
crop diagnosis conversation.

CONFIRMED FACTS:

Crop Name:
{crop_name}

Scientific Name:
{scientific_name}

Image Analysis:
{json.dumps(
    image_analysis,
    ensure_ascii=False,
    indent=2
)}

Diagnosis:
{json.dumps(
    diagnosis,
    ensure_ascii=False,
    indent=2
)}

STRICT RULES:

1. Crop name is already confirmed.
2. NEVER change crop name.
3. NEVER identify another crop.
4. NEVER say mango if crop is guava.
5. NEVER re-analyze the image.
6. Use diagnosis as context.
7. Answer only farmer question.
8. Use simple Hindi.
9. Use Indian agriculture practices.
10. Mention active ingredients
    instead of brand names.
"""

        messages = [

            {
                "role": "system",
                "content":
                    system_prompt,
            },

            {
                "role": "user",
                "content":
                    request.question,
            },
        ]

        answer = (
            llm_service.generate(
                messages=messages,
                temperature=0.1,
                max_tokens=800,
            )
        )

        chat_memory_service.save_message(
            thread_id=request.thread_id,
            role="user",
            message=request.question,
        )

        chat_memory_service.save_message(
            thread_id=request.thread_id,
            role="assistant",
            message=answer,
        )

        return {
            "success": True,
            "thread_id": request.thread_id,
            "crop_name": crop_name,
            "answer": answer,
        }

    except Exception as exc:

        logger.exception(
            "Image followup failed",
            error=str(exc),
        )

        return {
            "success": False,
            "error": str(exc),
        }