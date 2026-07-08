import json
import re

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.ai.cleaner import hindi_cleaner
from app.ai.extractor import information_extractor
from app.ai.generator import answer_generator
from app.ai.ranker import ranking_service
from app.ai.semantic_normalizer import semantic_normalizer

from app.schemas.request import AnalyzeRequest

from app.services.chat_memory_service import (
    chat_memory_service,
)

from app.services.conversation_service import (
    conversation_service,
)

from app.services.intent_validation_service import (
    intent_validation_service,
)

from app.services.memory_relevance_service import (
    memory_relevance_service,
)

from app.services.prompt_builder import (
    prompt_builder,
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

from app.core.logger import logger

router = APIRouter(tags=["Ask"])

RELEVANCE_THRESHOLD = 0.45


# =====================================
# SSE FORMATTER
# =====================================

def sse_event(data: dict) -> str:

    return (
        f"data: "
        f"{json.dumps(data, ensure_ascii=False)}"
        "\n\n"
    )


# =====================================
# TOKENIZER
# =====================================

def tokenize_stream_text(
    text: str,
) -> list[str]:

    """
    Regex tokenizer that preserves:
    - words
    - spaces
    - new lines
    - markdown boundaries
    """

    return re.findall(
        r"\n\n|\n|[^\s]+\s*",
        text,
    )


# =====================================
# ASK API
# =====================================

@router.post("/ask")
async def ask_question(
    request: AnalyzeRequest,
):

    async def event_generator():

        try:

            logger.info(
                "Ask request received",
                thread_id=request.thread_id,
            )

            # =====================================
            # IMMEDIATE REQUEST EVENT
            # =====================================

            yield sse_event(
                {
                    "event": "metadata",
                    "success": True,
                    "data": {
                        "thread_id": (
                            request.thread_id
                        ),
                        "query": (
                            request.text
                        ),
                    },
                }
            )

            # =====================================
            # SAVE USER MESSAGE
            # =====================================

            chat_memory_service.save_message(
                thread_id=request.thread_id,
                role="user",
                message=request.text,
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
            # CLEAN QUERY
            # =====================================

            cleaned_text = (
                hindi_cleaner.clean(
                    request.text
                )
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

            # =====================================
            # LOAD MEMORY
            # =====================================

            recent_messages = (
                chat_memory_service.get_recent_messages(
                    thread_id=request.thread_id,
                    limit=4,
                )
            )

            relevant_memory = (
                memory_relevance_service.filter_relevant_memory(
                    current_query=cleaned_text,
                    messages=recent_messages,
                    threshold=0.35,
                    max_messages=4,
                )
            )

            # =====================================
            # QUERY REWRITE
            # =====================================

            rewritten_query = (
                query_rewrite_service.rewrite(
                    current_query=cleaned_text,
                    memory_messages=(
                        relevant_memory
                    ),
                )
            )

            # =====================================
            # REWRITTEN ANALYSIS
            # =====================================

            rewritten_analysis = (
                information_extractor.extract(
                    rewritten_query
                )
            )

            rewritten_analysis["crop"] = (
                semantic_normalizer.normalize_crop(
                    rewritten_analysis.get(
                        "crop"
                    )
                )
            )

            # =====================================
            # RETRIEVAL
            # =====================================

            retrieval_results = (
                retrieval_pipeline.retrieve(
                    query=rewritten_query,
                    top_k=3,
                )
            )

            # =====================================
            # NO KNOWLEDGE
            # =====================================

            if not retrieval_results:

                yield sse_event(
                    {
                        "event": "fallback",
                        "success": True,
                        "data": {
                            "message": (
                                "No grounded knowledge found. "
                                "Using AI expert fallback."
                            ),
                            "is_grounded": False,
                        },
                    }
                )

                retrieval_results = []

            # =====================================
            # FILTER RESULTS
            # =====================================

            filtered_results = (
                retrieval_filter_service.filter_results(
                    results=retrieval_results,
                    query_analysis=(
                        rewritten_analysis
                    ),
                )
            )

            # =====================================
            # RANK RESULTS
            # =====================================

            ranked_results = (
                ranking_service.rank(
                    items=filtered_results,
                    query_context=(
                        rewritten_analysis
                    ),
                )
            )

            # =====================================
            # RELEVANCE FILTER
            # =====================================

            top_results = [

                item

                for item in ranked_results

                if item[
                    "ranking_score"
                ]
                >= RELEVANCE_THRESHOLD

            ][:3]

            # =====================================
            # INTENT VALIDATION
            # =====================================

            retrieved_text = " ".join(

                [
                    item.get(
                        "document",
                        "",
                    )
                    for item in top_results
                ]
            )

            intent_info = (
                intent_validation_service.validate(
                    query=cleaned_text,
                    retrieved_text=(
                        retrieved_text
                    ),
                )
            )

            # =====================================
            # BUILD PROMPT
            # =====================================

            final_prompt = (
                prompt_builder.build(
                    current_query=cleaned_text,
                    rag_contexts=top_results,
                    memory_messages=(
                        relevant_memory
                    ),
                    intent_info=(
                        intent_info
                    ),
                )
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
            # STREAMING GENERATION
            # =====================================

            full_answer = ""

            stream_buffer = ""

            for chunk in (
                answer_generator.stream_generate(
                    prompt=final_prompt,
                    results=top_results,
                )
            ):

                if not chunk:
                    continue

                full_answer += chunk

                stream_buffer += chunk

                # tokenize safely
                tokens = tokenize_stream_text(
                    stream_buffer
                )

                # keep last partial token
                if (
                    stream_buffer
                    and not stream_buffer.endswith(
                        (
                            " ",
                            "\n",
                        )
                    )
                ):

                    incomplete_token = (
                        tokens.pop()
                    )

                else:

                    incomplete_token = ""

                for token in tokens:

                    yield sse_event(
                        {
                            "event": "chunk",
                            "success": True,
                            "data": {
                                "content": token
                            },
                        }
                    )

                stream_buffer = (
                    incomplete_token
                )

            # =====================================
            # FINAL BUFFER
            # =====================================

            if stream_buffer:

                yield sse_event(
                    {
                        "event": "chunk",
                        "success": True,
                        "data": {
                            "content": (
                                stream_buffer
                            )
                        },
                    }
                )

            # =====================================
            # SAVE ASSISTANT MESSAGE
            # =====================================

            chat_memory_service.save_message(
                thread_id=request.thread_id,
                role="assistant",
                message=full_answer,
            )

            # =====================================
            # BEST SCORE
            # =====================================

            best_match_score = (

                top_results[0][
                    "ranking_score"
                ]

                if top_results

                else 0.0
            )

            # =====================================
            # SAVE CONVERSATION
            # =====================================

            conversation_service.save(
                input_type="text",
                original_query=request.text,
                cleaned_query=cleaned_text,
                transcription=None,
                analysis=rewritten_analysis,
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
                    "sources": (
                        top_results
                    )
                },
            )

            # =====================================
            # COMPLETE EVENT
            # =====================================

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

                        "rewritten_analysis": (
                            rewritten_analysis
                        ),

                        "intent_info": (
                            intent_info
                        ),

                        "retrieved_count": len(
                            retrieval_results
                        ),

                        "best_match_score": (
                            best_match_score
                        ),

                        "memory_used": len(
                            relevant_memory
                        ),

                        "contexts_used": len(
                            top_results
                        ),

                        "is_grounded": (
                            len(top_results)
                            > 0
                        ),

                        "answer": (
                            full_answer
                        ),

                        "sources": (
                            top_results
                        ),
                    },
                }
            )

            # =====================================
            # DONE EVENT
            # =====================================

            yield "data: [DONE]\n\n"

        except Exception as exc:

            logger.exception(
                "Streaming ask failed",
                error=str(exc),
            )

            yield sse_event(
                {
                    "event": "error",
                    "success": False,
                    "error": {

                        "code": (
                            "INTERNAL_SERVER_ERROR"
                        ),

                        "type": (
                            "server_error"
                        ),

                        "status_code": 500,

                        "message": (
                            "Internal server error"
                        ),

                        "details": str(exc),
                    },
                }
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
