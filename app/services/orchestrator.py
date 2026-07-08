from typing import Dict, Any

from app.agents.rag_agent import (
    rag_agent,
)

from app.agents.web_agent import (
    web_agent,
)

from app.services.response_synthesizer import (
    response_synthesizer,
)

from app.services.query_router_service import (
    query_router_service,
)

from app.core.logger import (
    logger,
)

from app.services.query_decomposer import (
    query_decomposer,
)
from app.services.agriculture_guardrail import (
    AgricultureGuardrail,
)

from app.core.agriculture_response import (
    AGRICULTURE_ONLY_RESPONSE,
)
class Orchestrator:

    # =====================================================
    # MAIN ORCHESTRATION
    # =====================================================

    async def process_query(
        self,
        query: str,
        thread_id: str = None,
    ) -> Dict[str, Any]:

        """
        Intelligent AI orchestration.

        ROUTES:
        - RAG
        - WEB
        - BOTH
        """

        # =================================================
        # AGRICULTURE GUARDRAIL
        # =================================================

        is_agri, confidence = (
            AgricultureGuardrail.validate(query)
        )

        logger.info(
            "Agriculture validation.",
            query=query,
            is_agri=is_agri,
            confidence=confidence,
        )

        if not is_agri or confidence < 0.80:

            logger.warning(
                "Non agriculture query blocked.",
                query=query,
            )

            return {

                "success": True,

                "route": "GUARDRAIL_BLOCK",

                "query": query,

                "response": AGRICULTURE_ONLY_RESPONSE,

                "sources": [],

                "confidence": confidence,

                "routing_reason": (
                    "Non agriculture query"
                ),
            }

        # =================================================
        # ROUTE DECISION (LLM BASED)
        # =================================================

        routing = await (
            query_router_service
            .decide_route(
                query=query,
            )
        )

        route = routing.get(
            "route",
            "RAG",
        ).upper()

        reason = routing.get(
            "reason",
            "",
        )

        logger.info(
            "FINAL ROUTE",
            route=route,
            reason=reason,
            query=query,
        )

        # =================================================
        # WEB ROUTE
        # =================================================

        if route == "WEB":

            logger.info(
                "WEB route triggered.",
                query=query,
            )

            web_result = await web_agent.run(
                query=query,
            )

            final_response = await (
                response_synthesizer
                .synthesize_web_response(
                    query=query,
                    web_results=(
                        web_result.get(
                            "results",
                            [],
                        )
                    ),
                )
            )

            return {

                "success": True,

                "route": "WEB",

                "query": query,

                "response": final_response,

                "sources": web_result.get(
                    "results",
                    [],
                ),

                "confidence": 1.0,

                "routing_reason": reason,
            }

        # =================================================
        # BOTH ROUTE
        # =================================================

        elif route == "BOTH":

            logger.info(
                "BOTH route triggered.",
                query=query,
            )

            rag_result = await rag_agent.run(
                query=query,
                thread_id=thread_id,
            )

            web_result = await web_agent.run(
                query=query,
            )

            rag_response = (
                rag_result.get(
                    "response",
                    "",
                )
            )

            web_results = (
                web_result.get(
                    "results",
                    [],
                )
            )

            final_response = await (
                response_synthesizer
                .synthesize_hybrid_response(
                    query=query,
                    rag_response=(
                        rag_response
                    ),
                    web_results=(
                        web_results
                    ),
                )
            )

            return {

                "success": True,

                "route": "BOTH",

                "query": query,

                "response": final_response,

                "sources": {

                    "rag_sources": (
                        rag_result.get(
                            "sources",
                            [],
                        )
                    ),

                    "web_sources": (
                        web_results
                    ),
                },

                "confidence": max(

                    rag_result.get(
                        "confidence",
                        0.0,
                    ),

                    0.80,
                ),

                "routing_reason": reason,

                "rag_response": (
                    rag_response
                ),
            }

        # =================================================
        # DEFAULT RAG ROUTE
        # =================================================

        logger.info(
            "RAG route triggered.",
            query=query,
        )

        rag_result = await rag_agent.run(
            query=query,
            thread_id=thread_id,
        )

        return {

            "success": True,

            "route": "RAG",

            "query": query,

            "response": rag_result.get(
                "response",
                "",
            ),

            "sources": rag_result.get(
                "sources",
                [],
            ),

            "confidence": rag_result.get(
                "confidence",
                0.0,
            ),

            "analysis": rag_result.get(
                "analysis",
                {},
            ),

            "plan": rag_result.get(
                "plan",
                {},
            ),

            "rewritten_query": rag_result.get(
                "rewritten_query",
                query,
            ),

            "routing_reason": reason,
        }


# =========================================================
# GLOBAL INSTANCE
# =========================================================

orchestrator = Orchestrator()