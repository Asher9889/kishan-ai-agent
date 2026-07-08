from app.ai.llm import (
    llm_service,
)

from app.core.logger import (
    logger,
)


class QueryIntentService:

    def classify(
        self,
        query: str,
    ) -> str:

        try:

            prompt = f"""
You are an intent classification system.

Your task is to classify the user query into EXACTLY one category.

Categories:

1. AGRICULTURE_QUERY
- crop disease
- fertilizer
- pesticide
- irrigation
- farming issue
- agriculture advice
- crop cultivation
- livestock
- soil
- weather impact on farming
- mandi related agriculture queries

2. NON_AGRICULTURE
- politics
- prime minister
- president
- sports
- cricket
- IPL
- celebrities
- movies
- history
- mathematics
- programming
- coding
- science
- current affairs
- general knowledge
- religion
- entertainment
- any topic not related to agriculture

3. META_QUERY
- asking where answer came from
- asking if answer is authentic
- asking about source
- asking if answer came from knowledge base
- asking if response is grounded

4. GREETING
- hello
- hi
- namaste

5. FOLLOW_UP
- follow-up question related to previous context

6. SMALL_TALK
- thank you
- okay
- casual conversation

Rules:
- Return ONLY category name
- No explanation
- No sentence
- No extra text
- If the query is NOT related to agriculture, return NON_AGRICULTURE
- When unsure, prefer NON_AGRICULTURE

Examples:

Query:
धान में रोग लग गया
Category:
AGRICULTURE_QUERY

Query:
गेहूं में यूरिया कब डालें
Category:
AGRICULTURE_QUERY

Query:
क्या ये answer knowledge base से आया है?
Category:
META_QUERY

Query:
hello
Category:
GREETING

Query:
ठीक है धन्यवाद
Category:
SMALL_TALK

Query:
Who is PM of India?
Category:
NON_AGRICULTURE

Query:
IPL winner kaun hai?
Category:
NON_AGRICULTURE

Query:
Python kya hai?
Category:
NON_AGRICULTURE

Query:
Taj Mahal kahan hai?
Category:
NON_AGRICULTURE

Query:
{query}

Category:
"""

            response = (
                llm_service.generate(
                    prompt
                )
            )

            intent = (
                response.strip()
                .replace("\n", "")
                .replace(".", "")
                .replace(":", "")
                .replace("-", "_")
                .replace(" ", "_")
                .upper()
            )

            valid_intents = [
                "AGRICULTURE_QUERY",
                "NON_AGRICULTURE",
                "META_QUERY",
                "GREETING",
                "FOLLOW_UP",
                "SMALL_TALK",
            ]

            if intent not in valid_intents:

                logger.warning(
                    "Invalid intent detected.",
                    raw_response=response,
                )

                return (
                    "AGRICULTURE_QUERY"
                )

            logger.info(
                "Intent classified.",
                intent=intent,
                query=query,
            )

            return intent

        except Exception as exc:

            logger.exception(
                "Intent classification failed.",
                error=str(exc),
            )

            return (
                "AGRICULTURE_QUERY"
            )


query_intent_service = (
    QueryIntentService()
)