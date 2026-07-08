from typing import List

from app.ai.llm import (
    llm_service,
)

from app.core.logger import (
    logger,
)


class ResponseSynthesizer:

    # =====================================================
    # WEB RESPONSE
    # =====================================================

    async def synthesize_web_response(
        self,
        query: str,
        web_results: List[dict],
    ) -> str:

        # =================================================
        # BUILD CONTEXT
        # =================================================

        context = ""

        for index, item in enumerate(
            web_results,
            start=1,
        ):

            title = item.get(
                "title",
                "",
            )

            snippet = item.get(
                "snippet",
                "",
            )

            context += f"""

RESULT {index}

Title:
{title}

Snippet:
{snippet}

"""

        # =================================================
        # PRODUCTION PROMPT
        # =================================================

        messages = [

            {
                "role": "system",
                "content": """
You are Krishi Anubhav AI.

You are a professional Indian agriculture assistant.

IMPORTANT RULES:

1. If live mandi price exists:
   answer directly.

2. NEVER say:
   - I cannot access live data
   - I do not know
   - contact market
   - check online

3. Extract best possible real value
from web search results.

4. If multiple prices exist:
   provide approximate range.

5. Keep answer SHORT.

6. Answer in Hindi.

7. NEVER ask follow-up questions.

8. Be confident.

9. Mention city name if available.

10. If exact rate unavailable:
give closest available rate from search results.
""",
            },

            {
                "role": "user",
                "content": f"""
User Query:
{query}

Web Search Results:
{context}

Generate final farmer-friendly answer.
""",
            },
        ]

        # =================================================
        # GENERATE
        # =================================================

        try:

            response = (
                llm_service.generate(
                    messages=messages,
                    temperature=0.2,
                    max_tokens=250,
                )
            )

            return response

        except Exception as exc:

            logger.exception(
                "Web synthesis failed.",
                error=str(exc),
            )

            return (
                "माफ़ कीजिए, अभी लाइव जानकारी "
                "उपलब्ध नहीं हो पाई।"
            )

    # =====================================================
    # HYBRID RESPONSE
    # =====================================================

    async def synthesize_hybrid_response(
        self,
        query: str,
        rag_response: str,
        web_results: List[dict],
    ) -> str:

        web_context = ""

        for item in web_results:

            web_context += f"""

Title:
{item.get("title", "")}

Snippet:
{item.get("snippet", "")}

"""

        messages = [

            {
                "role": "system",
                "content": """
You are Krishi Anubhav AI.

Merge:
1. Agriculture expert knowledge
2. Latest live web information

Give:
- practical
- accurate
- short
- Hindi response.
""",
            },

            {
                "role": "user",
                "content": f"""
User Query:
{query}

RAG Knowledge:
{rag_response}

Web Information:
{web_context}

Generate final answer.
""",
            },
        ]

        try:

            response = (
                llm_service.generate(
                    messages=messages,
                    temperature=0.3,
                    max_tokens=400,
                )
            )

            return response

        except Exception as exc:

            logger.exception(
                "Hybrid synthesis failed.",
                error=str(exc),
            )

            return rag_response


response_synthesizer = (
    ResponseSynthesizer()
)