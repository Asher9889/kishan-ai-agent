from typing import Dict, Any

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


RELEVANCE_THRESHOLD = 0.45


async def process_rag_query(
    query: str,
    thread_id: str = None,
) -> Dict[str, Any]:

    # =====================================
    # CLEAN QUERY
    # =====================================

    cleaned_text = (
        hindi_cleaner.clean(
            query
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
            thread_id=thread_id,
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
    # GENERATE RESPONSE
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
    # COLLECT STREAM RESPONSE
    # =====================================

    full_answer = ""

    for token in response_stream:

        full_answer += token

    # =====================================
    # CONFIDENCE
    # =====================================

    best_match_score = (
        top_results[0].get(
            "ranking_score",
            0.0,
        )
        if top_results
        else 0.0
    )

    return {

        "type": "RAG",

        "query": query,

        "cleaned_query": cleaned_text,

        "rewritten_query": rewritten_query,

        "response": full_answer,

        "sources": top_results,

        "confidence": best_match_score,

        "analysis": extracted_data,

        "plan": plan,
    }