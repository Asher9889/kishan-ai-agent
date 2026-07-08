import json

from app.ai.llm import (
    llm_service,
)

from app.core.logger import (
    logger,
)


class QueryRouterService:

    async def decide_route(
        self,
        query: str,
    ) -> dict:

        prompt = f"""
You are an intelligent routing AI.

Your task:
Classify the user query.

Possible routes:

1. RAG
Use when:
- agricultural knowledge
- crop disease
- fertilizer guidance
- pest management
- farming techniques
- irrigation
- static expert knowledge

2. WEB
Use when query requires:
- live mandi bhav
- current weather
- latest news
- government updates
- live market prices
- latest outbreak
- current location info
- real-time information

3. BOTH
Use when both:
- expert agricultural knowledge
AND
- latest live information
are required.

Return ONLY valid JSON.

Format:
{{
   "route":"RAG",
   "reason":"..."
}}

User Query:
{query}
"""

        try:

            response = llm_service.generate(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0,
                max_tokens=120,
            )

            parsed = json.loads(
                response
            )

            logger.info(
                "Route decided.",
                route=parsed,
            )

            return parsed

        except Exception as exc:

            logger.exception(
                "Routing failed.",
                error=str(exc),
            )

            return {
                "route": "RAG",
                "reason": "fallback",
            }


query_router_service = (
    QueryRouterService()
)