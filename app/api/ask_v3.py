# # from fastapi import (
# #     APIRouter,
# # )

# # from fastapi.responses import (
# #     StreamingResponse,
# # )

# # from app.schemas.request import (
# #     AnalyzeRequest,
# # )

# # from app.services.orchestrator_stream_service import (
# #     orchestrator_stream_service,
# # )


# # router = APIRouter(
# #     tags=["V3 Streaming"],
# # )


# # @router.post(
# #     "/v3/ask"
# # )
# # async def ask_v3(
# #     request: AnalyzeRequest,
# # ):

# #     return StreamingResponse(

# #         orchestrator_stream_service.stream(
# #             query=request.text,
# #             thread_id=request.thread_id,
# #         ),

# #         media_type="text/event-stream",
# #     )

# # ==================================================

# import json

# from fastapi import (
#     APIRouter,
# )

# from fastapi.responses import (
#     StreamingResponse,
# )

# from app.ai.cleaner import (
#     hindi_cleaner,
# )

# from app.ai.extractor import (
#     information_extractor,
# )

# from app.ai.semantic_normalizer import (
#     semantic_normalizer,
# )

# from app.ai.ranker import (
#     ranking_service,
# )

# from app.core.logger import (
#     logger,
# )

# from app.schemas.request import (
#     AnalyzeRequest,
# )

# from app.services.chat_memory_service import (
#     chat_memory_service,
# )

# from app.services.memory_relevance_service import (
#     memory_relevance_service,
# )

# from app.services.query_rewrite_service import (
#     query_rewrite_service,
# )

# from app.services.retrieval_pipeline import (
#     retrieval_pipeline,
# )

# from app.services.retrieval_filter_service import (
#     retrieval_filter_service,
# )

# from app.services.diagnostic_service import (
#     diagnostic_service,
# )

# from app.services.conversation_response_service import (
#     conversation_response_service,
# )

# from app.services.conversation_service import (
#     conversation_service,
# )

# from app.services.orchestrator import (
#     orchestrator,
# )
# from app.services.query_intent_service import (
#     query_intent_service,
# )

# router = APIRouter(
#     tags=["V3 Streaming"],
# )


# # =====================================================
# # SSE EVENT FORMATTER
# # =====================================================

# def sse_event(
#     data: dict,
# ) -> str:

#     return (
#         f"data: "
#         f"{json.dumps(data, ensure_ascii=False)}"
#         "\n\n"
#     )


# # =====================================================
# # V3 ASK API
# # =====================================================

# @router.post(
#     "/v3/ask"
# )
# async def ask_v3(
#     request: AnalyzeRequest,
# ):

#     async def token_generator():

#         try:
#             # =============================================
#             # SAVE USER MESSAGE
#             # =============================================

#             chat_memory_service.save_message(
#                 thread_id=request.thread_id,
#                 role="user",
#                 message=request.text,
#             )

#             # =============================================
#             # METADATA EVENT
#             # =============================================

#             yield sse_event(
#                 {
#                     "event": "metadata",
#                     "success": True,
#                     "data": {
#                         "thread_id": (
#                             request.thread_id
#                         ),
#                         "query": (
#                             request.text
#                         ),
#                     },
#                 }
#             )

#             # =============================================
#             # START EVENT
#             # =============================================

#             yield sse_event(
#                 {
#                     "event": "start",
#                     "success": True,
#                 }
#             )

#             # =============================================
#             # CLEAN QUERY
#             # =============================================

#             cleaned_text = (
#                 hindi_cleaner.clean(
#                     request.text
#                 )
#             )

#             logger.info(
#                 "Query cleaned.",
#                 query=cleaned_text,
#             )

#             # =============================================
#             # INTENT CLASSIFICATION
#             # =============================================

#             intent = query_intent_service.classify(
#                 cleaned_text
#             )

#             logger.info(
#                 "Query intent classified.",
#                 intent=intent,
#             )

#             # =============================================
#             # NON AGRICULTURE GUARDRAIL
#             # =============================================

#             if intent == "NON_AGRICULTURE":

#                 answer = (
#                     "मैं कृषि अनुभाव AI हूँ। "
#                     "मैं केवल कृषि एवं किसान संबंधित प्रश्नों का उत्तर दे सकता हूँ। "
#                     "कृपया फसल, रोग, कीट, खाद, सिंचाई या कृषि विषयक प्रश्न पूछें।"
#                 )

#                 # response save
#                 chat_memory_service.save_message(
#                     thread_id=request.thread_id,
#                     role="assistant",
#                     message=answer,
#                 )

#                 yield sse_event(
#                     {
#                         "event": "chunk",
#                         "success": True,
#                         "data": {
#                             "content": answer
#                         },
#                     }
#                 )

#                 yield sse_event(
#                     {
#                         "event": "complete",
#                         "success": True,
#                         "data": {
#                             "thread_id": request.thread_id,
#                             "query": cleaned_text,
#                             "intent": intent,
#                             "answer": answer,
#                             "route": "BLOCKED",
#                         },
#                     }
#                 )

#                 yield "data: [DONE]\n\n"

#                 return
        
#             # =============================================
#             # MEMORY
#             # =============================================

#             recent_messages = (
#                 chat_memory_service.get_recent_messages(
#                     thread_id=request.thread_id,
#                     limit=10,
#                 )
#             )

#             relevant_memory = (
#                 memory_relevance_service.filter_relevant_memory(
#                     current_query=cleaned_text,
#                     messages=recent_messages,
#                     threshold=0.40,
#                     max_messages=6,
#                 )
#             )
#             working_memory = (
#                 chat_memory_service.build_working_memory(
#                     recent_messages=recent_messages
#                 )
#             )

#             # =============================================
#             # EXTRACTION
#             # =============================================

#             extracted_data = (
#                 information_extractor.extract(
#                     cleaned_text
#                 )
#             )

#             extracted_data["crop"] = (
#                 semantic_normalizer.normalize_crop(
#                     extracted_data.get(
#                         "crop"
#                     )
#                 )
#             )
#             reference_words = [

#             "इसकी",
#             "इसका",
#             "इसके",
#             "उसकी",
#             "उसका",
#             "उसके",
#             "उसमें",
#             "इसमें",
#             "वही",
#             "वो",
#         ]

#         is_reference_query = any(
#             word in cleaned_text
#             for word in reference_words
#         )

#         if (
#             is_reference_query
#             and not extracted_data.get("crop")
#         ):
#             extracted_data["crop"] = (
#                 working_memory.get(
#                     "active_crop"
#                 )
#             )

#             logger.info(
#                 "Crop restored from memory.",
#                 crop=extracted_data["crop"],
#             )
#             # =============================================
#             # QUERY REWRITE
#             # =============================================

#             if (
#                 extracted_data.get("crop")
#                 and is_reference_query
#             ):

#                 rewritten_query = (
#                     f"{extracted_data['crop']} "
#                     f"{cleaned_text}"
#                 )

#             else:

#                 rewritten_query = (
#                     query_rewrite_service.rewrite(
#                         current_query=cleaned_text,
#                         memory_messages=relevant_memory,
#                     )
#                 )

#             # =============================================
#             # PLAN
#             # =============================================

#             plan = (
#                 diagnostic_service
#                 .decide_response_mode(
#                     query=cleaned_text,
#                     analysis=extracted_data,
#                     memory=relevant_memory,
#                 )
#             )

#             # =============================================
#             # PROCESSING EVENT
#             # =============================================

#             yield sse_event(
#                 {
#                     "event": "processing",
#                     "success": True,
#                 }
#             )

#             # =============================================
#             # ORCHESTRATOR
#             # =============================================

#             result = await orchestrator.process_query(
#                 query=cleaned_text,
#                 thread_id=request.thread_id,
#             )

#             # =============================================
#             # SOURCES
#             # =============================================

#             sources = result.get(
#                 "sources",
#                 [],
#             )

#             # =============================================
#             # RETRIEVED COUNT
#             # =============================================

#             retrieved_count = len(
#                 sources
#             )

#             # =============================================
#             # CONFIDENCE
#             # =============================================

#             confidence = result.get(
#                 "confidence",
#                 0.0,
#             )

#             # =============================================
#             # AI START
#             # =============================================

#             yield sse_event(
#                 {
#                     "event": "ai_start",
#                     "success": True,
#                 }
#             )

#             # =============================================
#             # STREAM RESPONSE
#             # =============================================

#             answer = result.get(
#                 "response",
#                 "",
#             )

#             buffer = ""

#             for token in answer:

#                 buffer += token

#                 if (
#                     token == " "
#                     or token == "\n"
#                 ):

#                     if buffer.strip():

#                         yield sse_event(
#                             {
#                                 "event": "chunk",
#                                 "success": True,
#                                 "data": {
#                                     "content": buffer
#                                 },
#                             }
#                         )

#                     buffer = ""

#             # =============================================
#             # FLUSH LAST BUFFER
#             # =============================================

#             if buffer.strip():

#                 yield sse_event(
#                     {
#                         "event": "chunk",
#                         "success": True,
#                         "data": {
#                             "content": buffer
#                         },
#                     }
#                 )
            
#             # =============================================
#             # SAVE ASSISTANT RESPONSE
#             # =============================================

#             chat_memory_service.save_message(
#                 thread_id=request.thread_id,
#                 role="assistant",
#                 message=answer,
#             )

#             logger.info(
#                 "Assistant response saved."
#             )
#             # =============================================
#             # SAVE CONVERSATION
#             # =============================================

#             try:

#                 conversation_service.save(
#                 input_type="text",
#                 original_query=request.text,
#                 cleaned_query=cleaned_text,
#                 transcription=None,
#                 analysis=extracted_data,
#                 retrieved_count=retrieved_count,
#                 best_match_score=confidence,
#                 final_answer=answer,
#                 answer_confidence=confidence,
#                 source={
#                     "sources": sources
#                 },
#             )

#             except Exception as exc:

#                 logger.exception(
#                     "Conversation save failed.",
#                     error=str(exc),
#                 )

#             # =============================================
#             # COMPLETE EVENT
#             # =============================================

#             yield sse_event(
#                 {
#                     "event": "complete",
#                     "success": True,
#                     "data": {

#                         # =================================
#                         # QUERY
#                         # =================================

#                         "thread_id": (
#                             request.thread_id
#                         ),

#                         "query": (
#                             cleaned_text
#                         ),

#                         "rewritten_query": (
#                             rewritten_query
#                         ),

#                         # =================================
#                         # ANALYSIS
#                         # =================================

#                         "analysis": (
#                             extracted_data
#                         ),

#                         # =================================
#                         # RETRIEVAL
#                         # =================================

#                         "retrieved_count": (
#                             retrieved_count
#                         ),

#                         "contexts_used": (
#                             retrieved_count
#                         ),

#                         # =================================
#                         # MEMORY
#                         # =================================

#                         "memory_used": len(
#                             relevant_memory
#                         ),

#                         # =================================
#                         # CONFIDENCE
#                         # =================================

#                         "best_match_score": (
#                             confidence
#                         ),

#                         "is_grounded": (
#                             retrieved_count > 0
#                         ),

#                         # =================================
#                         # SOURCES
#                         # =================================

#                         "sources": (
#                             sources
#                         ),

#                         # =================================
#                         # ANSWER
#                         # =================================

#                         "answer": (
#                             answer
#                         ),

#                         # =================================
#                         # PLAN
#                         # =================================

#                         "plan": (
#                             plan
#                         ),

#                         # =================================
#                         # ROUTE
#                         # =================================

#                         "route": result.get(
#                             "route",
#                             "RAG",
#                         ),
#                     },
#                 }
#             )

#             # =============================================
#             # DONE
#             # =============================================

#             yield (
#                 "data: [DONE]\n\n"
#             )

#         except Exception as exc:

#             logger.exception(
#                 "V3 stream failed.",
#                 error=str(exc),
#             )

#             yield sse_event(
#                 {
#                     "event": "error",
#                     "success": False,
#                     "message": str(exc),
#                 }
#             )

#             yield (
#                 "data: [DONE]\n\n"
#             )

#     return StreamingResponse(
#         token_generator(),
#         media_type="text/event-stream",
#     )

# ========================================================

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.ai.cleaner import hindi_cleaner
from app.ai.extractor import information_extractor
from app.ai.semantic_normalizer import semantic_normalizer
from app.ai.ranker import ranking_service
from app.core.logger import logger
from app.schemas.request import AnalyzeRequest
from app.services.chat_memory_service import chat_memory_service
from app.services.memory_relevance_service import memory_relevance_service
from app.services.query_rewrite_service import query_rewrite_service
from app.services.retrieval_pipeline import retrieval_pipeline
from app.services.retrieval_filter_service import retrieval_filter_service
from app.services.diagnostic_service import diagnostic_service
from app.services.conversation_response_service import conversation_response_service
from app.services.conversation_service import conversation_service
from app.services.orchestrator import orchestrator
from app.services.query_intent_service import query_intent_service
from app.services.agriculture_guardrail import (
    AgricultureGuardrail,
)

from app.core.agriculture_response import (
    AGRICULTURE_ONLY_RESPONSE,
)

router = APIRouter(tags=["V3 Streaming"])


# =====================================================
# SSE EVENT FORMATTER
# =====================================================
def sse_event(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# =====================================================
# V3 ASK API
# =====================================================
@router.post("/v3/ask")
async def ask_v3(request: AnalyzeRequest):
    async def token_generator():
        try:
            # =============================================
            # SAVE USER MESSAGE
            # =============================================
            chat_memory_service.save_message(
                thread_id=request.thread_id,
                role="user",
                message=request.text,
            )

            # =============================================
            # METADATA EVENT
            # =============================================
            yield sse_event({
                "event": "metadata",
                "success": True,
                "data": {
                    "thread_id": request.thread_id,
                    "query": request.text,
                },
            })

            # =============================================
            # START EVENT
            # =============================================
            yield sse_event({
                "event": "start",
                "success": True,
            })

            # =============================================
            # CLEAN QUERY
            # =============================================
            cleaned_text = hindi_cleaner.clean(request.text)
            logger.info("Query cleaned.", query=cleaned_text)

            # =============================================
            # INTENT CLASSIFICATION
            # =============================================
            intent = query_intent_service.classify(cleaned_text)
            # logger.info("Query intent classified.", intent=intent)
            logger.info(
                "FINAL INTENT",
                query=cleaned_text,
                intent=intent,
            )
            # =============================================
            # AGRICULTURE GUARDRAIL
            # =============================================
            is_agri, confidence = AgricultureGuardrail.validate(
                cleaned_text
            )

            logger.info(
                "Agriculture validation",
                is_agri=is_agri,
                confidence=confidence,
            )

            if not is_agri or confidence < 0.80:

                answer = AGRICULTURE_ONLY_RESPONSE

                chat_memory_service.save_message(
                    thread_id=request.thread_id,
                    role="assistant",
                    message=answer,
                )

                yield sse_event({
                    "event": "chunk",
                    "success": True,
                    "data": {
                        "content": answer
                    },
                })

                yield sse_event({
                    "event": "complete",
                    "success": True,
                    "data": {
                        "thread_id": request.thread_id,
                        "query": cleaned_text,
                        "answer": answer,
                        "route": "GUARDRAIL_BLOCK",
                    },
                })

                yield "data: [DONE]\n\n"
                return

            # =============================================
            # NON AGRICULTURE GUARDRAIL
            # =============================================
            if intent == "NON_AGRICULTURE":
                answer = (
                    "मैं कृषि अनुभाव AI हूँ। "
                    "मैं केवल कृषि एवं किसान संबंधित प्रश्नों का उत्तर दे सकता हूँ। "
                    "कृपया फसल, रोग, कीट, खाद, सिंचाई या कृषि विषयक प्रश्न पूछें।"
                )

                chat_memory_service.save_message(
                    thread_id=request.thread_id,
                    role="assistant",
                    message=answer,
                )

                yield sse_event({
                    "event": "chunk",
                    "success": True,
                    "data": {"content": answer},
                })

                yield sse_event({
                    "event": "complete",
                    "success": True,
                    "data": {
                        "thread_id": request.thread_id,
                        "query": cleaned_text,
                        "intent": intent,
                        "answer": answer,
                        "route": "BLOCKED",
                    },
                })

                yield "data: [DONE]\n\n"
                return

            # =============================================
            # MEMORY
            # =============================================
            recent_messages = chat_memory_service.get_recent_messages(
                thread_id=request.thread_id,
                limit=10,
            )

            relevant_memory = memory_relevance_service.filter_relevant_memory(
                current_query=cleaned_text,
                messages=recent_messages,
                threshold=0.40,
                max_messages=6,
            )

            working_memory = chat_memory_service.build_working_memory(
                recent_messages=recent_messages
            )

            # =============================================
            # EXTRACTION
            # =============================================
            extracted_data = information_extractor.extract(cleaned_text)
            extracted_data["crop"] = semantic_normalizer.normalize_crop(
                extracted_data.get("crop")
            )

            reference_words = [
                "इसकी", "इसका", "इसके",
                "उसकी", "उसका", "उसके",
                "उसमें", "इसमें", "वही", "वो",
            ]
            is_reference_query = any(word in cleaned_text for word in reference_words)

            # Restore crop from memory if needed
            if is_reference_query and not extracted_data.get("crop"):
                extracted_data["crop"] = working_memory.get("active_crop")
                logger.info("Crop restored from memory.", crop=extracted_data["crop"])

            # =============================================
            # QUERY REWRITE
            # =============================================
            if extracted_data.get("crop") and is_reference_query:
                rewritten_query = f"{extracted_data['crop']} {cleaned_text}"
            else:
                rewritten_query = query_rewrite_service.rewrite(
                    current_query=cleaned_text,
                    memory_messages=relevant_memory,
                )

            # =============================================
            # PLAN
            # =============================================
            plan = diagnostic_service.decide_response_mode(
                query=cleaned_text,
                analysis=extracted_data,
                memory=relevant_memory,
            )

            # =============================================
            # PROCESSING EVENT
            # =============================================
            yield sse_event({
                "event": "processing",
                "success": True,
            })

            # =============================================
            # ORCHESTRATOR
            # =============================================
            result = await orchestrator.process_query(
                query=rewritten_query,
                thread_id=request.thread_id,
            )

            sources = result.get("sources", [])
            retrieved_count = len(sources)
            confidence = result.get("confidence", 0.0)

            # =============================================
            # AI START
            # =============================================
            yield sse_event({
                "event": "ai_start",
                "success": True,
            })

            # =============================================
            # STREAM RESPONSE
            # =============================================
            answer = result.get("response", "")
            buffer = ""

            for token in answer:
                buffer += token
                if token == " " or token == "\n":
                    if buffer.strip():
                        yield sse_event({
                            "event": "chunk",
                            "success": True,
                            "data": {"content": buffer},
                        })
                    buffer = ""

            # Flush remaining buffer
            if buffer.strip():
                yield sse_event({
                    "event": "chunk",
                    "success": True,
                    "data": {"content": buffer},
                })

            # =============================================
            # SAVE ASSISTANT RESPONSE
            # =============================================
            chat_memory_service.save_message(
                thread_id=request.thread_id,
                role="assistant",
                message=answer,
            )
            logger.info("Assistant response saved.")

            # =============================================
            # SAVE CONVERSATION
            # =============================================
            try:
                conversation_service.save(
                    input_type="text",
                    original_query=request.text,
                    cleaned_query=cleaned_text,
                    transcription=None,
                    analysis=extracted_data,
                    retrieved_count=retrieved_count,
                    best_match_score=confidence,
                    final_answer=answer,
                    answer_confidence=confidence,
                    source={"sources": sources},
                )
            except Exception as exc:
                logger.exception("Conversation save failed.", error=str(exc))

            # =============================================
            # COMPLETE EVENT
            # =============================================
            yield sse_event({
                "event": "complete",
                "success": True,
                "data": {
                    "thread_id": request.thread_id,
                    "query": cleaned_text,
                    "rewritten_query": rewritten_query,
                    "analysis": extracted_data,
                    "retrieved_count": retrieved_count,
                    "contexts_used": retrieved_count,
                    "memory_used": len(relevant_memory),
                    "best_match_score": confidence,
                    "is_grounded": retrieved_count > 0,
                    "sources": sources,
                    "answer": answer,
                    "plan": plan,
                    "route": result.get("route", "RAG"),
                },
            })

            yield "data: [DONE]\n\n"

        except Exception as exc:
            logger.exception("V3 stream failed.", error=str(exc))
            yield sse_event({
                "event": "error",
                "success": False,
                "message": str(exc),
            })
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
    )