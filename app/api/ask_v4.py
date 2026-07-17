import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.request import AnalyzeRequest
from app.services.chat_memory_service import (
    chat_memory_service,
)

from app.services.orchestrator import (
    orchestrator,
)
from app.core.logger import (
    logger,
)
from app.services.voice_formatter import (
    voice_formatter,
)
from app.services.sentence_streamer import (
    sentence_streamer,
)

router = APIRouter(
    tags=["V4 Streaming"],
)



def sse_event(data: dict) -> str:
    return (
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


@router.post("/v4/ask")
async def ask_v4(
    request: AnalyzeRequest,
):

    async def token_generator():

        # =============================================
        # SAVE USER MESSAGE
        # =============================================

        chat_memory_service.save_message(
            thread_id=request.thread_id,
            role="user",
            message=request.text,
        )
        yield sse_event({
            "event": "metadata",
            "success": True,
            "data": {
                "thread_id": request.thread_id,
                "query": request.text,
            },
        })
        yield sse_event({

            "event": "start",

            "success": True,

        })
        try:

            result = await orchestrator.process_query(
                query=request.text,
                thread_id=request.thread_id,
            )

            # =============================================
            # GET ANSWER
            # =============================================

            answer = result.get(
                "response",
                "",
            )

            answer = voice_formatter.format(
                question=request.text,
                answer=answer,
                thread_id=request.thread_id,
            )

            # # =============================================
            # # STREAM ANSWER
            # # =============================================

            # yield sse_event(
            #     {
            #         "event": "chunk",
            #         "success": True,
            #         "data": {
            #             "content": answer,
            #         },
            #     }
            # )
            # =============================================
            # STREAM ANSWER SENTENCE BY SENTENCE
            # =============================================

            sentence_streamer.reset()

            for sentence in sentence_streamer.push(answer):

                yield sse_event(
                    {
                        "event": "chunk",
                        "success": True,
                        "data": {
                            "content": sentence,
                        },
                    }
                )

            for sentence in sentence_streamer.flush():

                yield sse_event(
                    {
                        "event": "chunk",
                        "success": True,
                        "data": {
                            "content": sentence,
                        },
                    }
                )
            # =============================================
            # COMPLETE EVENT
            # =============================================

            yield sse_event(
                {
                    "event": "complete",
                    "success": True,
                    "data": {
                        "thread_id": request.thread_id,
                        "answer": answer,
                    },
                }
            )

        except Exception as e:

            logger.exception(
                "V4 processing failed.",
            )

            yield sse_event(
                {
                    "event": "error",
                    "success": False,
                    "message": str(e),
                }
            )

            yield "data: [DONE]\n\n"

            return

        yield "data: [DONE]\n\n"
    return StreamingResponse(

        token_generator(),

        media_type="text/event-stream",

    )