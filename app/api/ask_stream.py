import json

from fastapi import (
    APIRouter,
)

from fastapi.responses import (
    StreamingResponse,
)

from app.ai.cleaner import (
    hindi_cleaner,
)

from app.ai.extractor import (
    information_extractor,
)

from app.ai.semantic_normalizer import (
    semantic_normalizer,
)

from app.ai.ranker import (
    ranking_service,
)

from app.core.logger import (
    logger,
)

from app.schemas.request import (
    AnalyzeRequest,
)

from app.services.chat_memory_service import (
    chat_memory_service,
)

from app.services.memory_relevance_service import (
    memory_relevance_service,
)

from app.services.query_rewrite_service import (
    query_rewrite_service,
)

from app.services.retrieval_pipeline import (
    retrieval_pipeline,
)

from app.services.retrieval_filter_service import (
    retrieval_filter_service,
)

from app.services.diagnostic_service import (
    diagnostic_service,
)

from app.services.conversation_response_service import (
    conversation_response_service,
)

from app.services.conversation_service import (
    conversation_service,
)


router = APIRouter(
    tags=["Streaming"],
)


RELEVANCE_THRESHOLD = 0.45


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


# =========================================
# ASK STREAM API
# =========================================

@router.post(
    "/v2/ask"
)
async def ask_stream(
    request: AnalyzeRequest,
):

    # =====================================
    # SAVE USER MESSAGE
    # =====================================

    chat_memory_service.save_message(
        thread_id=request.thread_id,
        role="user",
        message=request.text,
    )

    # =====================================
    # CLEAN QUERY
    # =====================================

    cleaned_text = (
        hindi_cleaner.clean(
            request.text
        )
    )

    logger.info(
        "Query cleaned.",
        query=cleaned_text,
    )

    # =====================================
    # LOAD MEMORY
    # =====================================

    recent_messages = (
        chat_memory_service.get_recent_messages(
            thread_id=request.thread_id,
            limit=10,
        )
    )

    relevant_memory = (
        memory_relevance_service.filter_relevant_memory(
            current_query=cleaned_text,
            messages=recent_messages,
            threshold=0.40,
            max_messages=6,
        )
    )

    logger.info(
        "Relevant memory selected.",
        count=len(
            relevant_memory
        ),
    )

    # =====================================
    # EXTRACTION
    # =====================================

    extracted_data = (
        information_extractor.extract(
            cleaned_text
        )
    )

    extracted_data["crop"] = (
        semantic_normalizer.normalize_crop(
            extracted_data.get(
                "crop"
            )
        )
    )

    logger.info(
        "Extraction completed.",
        extraction=extracted_data,
    )

    # =====================================
    # QUERY REWRITE
    # =====================================

    rewritten_query = (
        query_rewrite_service.rewrite(
            current_query=cleaned_text,
            memory_messages=relevant_memory,
        )
    )

    logger.info(
        "Query rewritten.",
        rewritten_query=(
            rewritten_query
        ),
    )

    # =====================================
    # DIAGNOSTIC PLAN
    # =====================================

    plan = (
        diagnostic_service
        .decide_response_mode(
            query=cleaned_text,
            analysis=extracted_data,
            memory=relevant_memory,
        )
    )

    logger.info(
        "Conversation plan created.",
        plan=plan,
    )

    # =====================================
    # RETRIEVAL
    # =====================================

    retrieval_results = (
        retrieval_pipeline.retrieve(
            query=rewritten_query,
            query_analysis=(
                extracted_data
            ),
            top_k=4,
        )
    )

    logger.info(
        "Retrieval completed.",
        results=len(
            retrieval_results
        ),
    )

    # =====================================
    # FILTER RESULTS
    # =====================================

    filtered_results = (
        retrieval_filter_service.filter_results(
            results=retrieval_results,
            query_analysis=(
                extracted_data
            ),
        )
    )

    logger.info(
        "Retrieval filtering completed.",
        filtered=len(
            filtered_results
        ),
    )

    # =====================================
    # RERANK RESULTS
    # =====================================

    ranked_results = (
        ranking_service.rank(
            items=filtered_results,
            query_context=(
                extracted_data
            ),
            top_k=2,
        )
    )

    logger.info(
        "Ranking completed.",
        ranked=len(
            ranked_results
        ),
    )

    # =====================================
    # FINAL GROUNDED RESULTS
    # =====================================

    top_results = [
        item
        for item in ranked_results
        if item.get(
            "ranking_score",
            0,
        ) >= RELEVANCE_THRESHOLD
    ]

    # =====================================
    # RESPONSE STREAM
    # =====================================

    response_stream = (

        conversation_response_service
        .stream_response(
            current_query=cleaned_text,
            memory_messages=(
                relevant_memory
            ),
            retrieval_results=(
                top_results
            ),
            plan=plan,
        )

    )

    # =====================================
    # TOKEN GENERATOR
    # =====================================

    async def token_generator():

        full_answer = ""

        try:

            # =================================
            # METADATA EVENT
            # =================================

            yield sse_event(
                {
                    "event": "metadata",
                    "success": True,
                    "data": {
                        "thread_id": (
                            request.thread_id
                        ),
                        "query": (
                            cleaned_text
                        ),
                    },
                }
            )

            # =================================
            # START EVENT
            # =================================

            yield sse_event(
                {
                    "event": "start",
                    "success": True,
                }
            )

            # =================================
            # PROCESSING EVENT
            # =================================

            yield sse_event(
                {
                    "event": "processing",
                    "success": True,
                }
            )

            # =================================
            # AI START EVENT
            # =================================

            yield sse_event(
                {
                    "event": "ai_start",
                    "success": True,
                }
            )

            # =================================
            # STREAM TOKENS
            # =================================

        
            # =================================
            # STREAM TOKENS (WORD CHUNKING)
            # =================================

            buffer = ""

            for token in response_stream:

                full_answer += token
                buffer += token

                # =========================
                # EMIT COMPLETE WORD
                # =========================

                if (
                    " " in buffer
                    or "\n" in buffer
                ):

                    parts = (
                        buffer.split(" ")
                    )

                    # emit all complete words
                    for part in parts[:-1]:

                        if part.strip():

                            yield sse_event(
                                {
                                    "event": "chunk",
                                    "success": True,
                                    "data": {
                                        "content": (
                                            part + " "
                                        )
                                    },
                                }
                            )

                    # keep incomplete word
                    buffer = parts[-1]

            # =================================
            # FLUSH REMAINING BUFFER
            # =================================

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


            # =================================
            # SAVE ASSISTANT RESPONSE
            # =================================

            chat_memory_service.save_message(
                thread_id=request.thread_id,
                role="assistant",
                message=full_answer,
            )

            logger.info(
                "Assistant response saved."
            )

            # =================================
            # BEST MATCH SCORE
            # =================================

            best_match_score = (
                top_results[0].get(
                    "ranking_score",
                    0.0,
                )
                if top_results
                else 0.0
            )

            # =================================
            # SAVE CONVERSATION
            # =================================

            conversation_service.save(
                input_type="text",
                original_query=request.text,
                cleaned_query=cleaned_text,
                transcription=None,
                analysis=extracted_data,
                retrieved_count=len(
                    retrieval_results
                ),
                best_match_score=(
                    best_match_score
                ),
                final_answer=full_answer,
                answer_confidence=(
                    best_match_score
                ),
                source={
                    "sources": top_results
                },
            )

            # =================================
            # COMPLETE EVENT
            # =================================

            yield sse_event(
                {
                    "event": "complete",
                    "success": True,
                    "data": {
                        "thread_id": (
                            request.thread_id
                        ),
                        "query": (
                            cleaned_text
                        ),
                        "rewritten_query": (
                            rewritten_query
                        ),
                        "analysis": (
                            extracted_data
                        ),
                        "retrieved_count": len(
                            retrieval_results
                        ),
                        "contexts_used": len(
                            top_results
                        ),
                        "memory_used": len(
                            relevant_memory
                        ),
                        "best_match_score": (
                            best_match_score
                        ),
                        "is_grounded": (
                            len(top_results)
                            > 0
                        ),
                        "sources": (
                            top_results
                        ),
                        "answer": (
                            full_answer
                        ),
                        "plan": (
                            plan
                        ),
                    },
                }
            )

            # =================================
            # DONE EVENT
            # =================================

            yield "data: [DONE]\n\n"

        except Exception as exc:

            logger.exception(
                "Streaming failed.",
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

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
    )
