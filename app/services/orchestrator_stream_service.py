import json

from app.core.logger import (
    logger,
)

from app.services.orchestrator import (
    orchestrator,
)


# =========================================
# SSE EVENT FORMATTER
# =========================================

def sse_event(
    data: dict,
) -> str:

    return (
        f"data: "
        f"{json.dumps(data, ensure_ascii=False)}"
        "\n\n"
    )


class OrchestratorStreamService:

    async def stream(
        self,
        query: str,
        thread_id: str = None,
    ):

        try:

            # =====================================
            # METADATA EVENT
            # =====================================

            yield sse_event(
                {
                    "event": "metadata",
                    "success": True,
                    "data": {
                        "thread_id": thread_id,
                        "query": query,
                    },
                }
            )

            # =====================================
            # START EVENT
            # =====================================

            yield sse_event(
                {
                    "event": "start",
                    "success": True,
                }
            )

            # =====================================
            # PROCESSING EVENT
            # =====================================

            yield sse_event(
                {
                    "event": "processing",
                    "success": True,
                }
            )

            # =====================================
            # AI START EVENT
            # =====================================

            yield sse_event(
                {
                    "event": "ai_start",
                    "success": True,
                }
            )

            # =====================================
            # ORCHESTRATOR
            # =====================================

            result = await orchestrator.process_query(
                query=query,
                thread_id=thread_id,
            )

            answer = result.get(
                "response",
                "",
            )

            # =====================================
            # STREAM TOKENS
            # =====================================

            buffer = ""

            for token in answer:

                buffer += token

                if (
                    token == " "
                    or token == "\n"
                ):

                    if buffer.strip():

                        yield sse_event(
                            {
                                "event": "chunk",
                                "success": True,
                                "data": {
                                    "content": buffer
                                },
                            }
                        )

                    buffer = ""

            # =====================================
            # FLUSH BUFFER
            # =====================================

            if buffer.strip():

                yield sse_event(
                    {
                        "event": "chunk",
                        "success": True,
                        "data": {
                            "content": buffer
                        },
                    }
                )

            # =====================================
            # COMPLETE EVENT
            # =====================================

            yield sse_event(
                {
                    "event": "complete",
                    "success": True,
                    "data": result,
                }
            )

            # =====================================
            # DONE EVENT
            # =====================================

            yield "data: [DONE]\n\n"

        except Exception as exc:

            logger.exception(
                "Orchestrator stream failed.",
                error=str(exc),
            )

            yield sse_event(
                {
                    "event": "error",
                    "success": False,
                    "message": str(exc),
                }
            )

            yield "data: [DONE]\n\n"


orchestrator_stream_service = (
    OrchestratorStreamService()
)