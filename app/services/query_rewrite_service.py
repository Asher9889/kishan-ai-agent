# File: app/services/query_rewrite_service.py

from typing import Any

from app.ai.llm import llm_service
from app.core.logger import logger


class QueryRewriteService:

    # =====================================
    # FORMAT MEMORY
    # =====================================

    def _format_memory(
        self,
        memory_messages: list[dict[str, Any]],
    ) -> str:

        memory_lines = []

        for message in memory_messages:

            role = message.get(
                "role",
                "user",
            )

            content = message.get(
                "message",
                "",
            )

            if content:
                memory_lines.append(
                    f"{role}: {content}"
                )

        return "\n".join(memory_lines)

    # =====================================
    # DETECT CLEAR QUERY
    # =====================================

    def _is_clear_query(
        self,
        query: str,
    ) -> bool:

        query_lower = query.lower()

        direct_keywords = [
            "क्या बताते हैं",
            "क्या कहा",
            "सलाह",
            "जानकारी",
            "कैसे करें",
            "इलाज",
            "समस्या",
            "कीट",
            "रोग",
            "खेती",
            "फसल",
        ]

        reference_words = [
            "उसमें",
            "वही",
            "उसका",
            "पहले वाला",
            "वहाँ",
            "कितना",
            "कौन सा",
        ]

        has_reference = any(
            word in query_lower
            for word in reference_words
        )

        has_direct_context = any(
            keyword in query_lower
            for keyword in direct_keywords
        )

        # already meaningful query

        if (
            has_direct_context
            and not has_reference
        ):
            return True

        return False

    # =====================================
    # REWRITE QUERY
    # =====================================

    def rewrite(
        self,
        *,
        current_query: str,
        memory_messages: list[dict[str, Any]],
    ) -> str:

        current_query = (
            current_query.strip()
        )

        # =================================
        # DO NOT REWRITE
        # =================================

        if (
            len(
                current_query.split()
            )
            >= 15
        ):
            return current_query

        if self._is_clear_query(
            current_query
        ):

            logger.info(
                "Skipping rewrite. Query already clear.",
                query=current_query,
            )

            return current_query

        # =================================
        # MEMORY
        # =================================

        memory_block = (
            self._format_memory(
                memory_messages
            )
        )

        # =================================
        # PROMPT
        # =================================

        messages = [
            {
                "role": "system",
                "content": """
You are an agricultural retrieval query rewriter.

Your ONLY job:
resolve conversational references.

IMPORTANT:

1. Preserve farmer names.
2. Preserve crop names.
3. Preserve locations.
4. Preserve disease/problem names.
5. Preserve retrieval intent.
6. NEVER convert information query into diagnosis query.
7. NEVER invent symptoms.
8. NEVER invent crops.
9. NEVER change meaning.
10. Keep rewritten query concise.

Rewrite ONLY if necessary.

Examples:

GOOD:
"उसमें क्या डालें"
→ "गेहूं में क्या डालें"

GOOD:
"वो किसान क्या बताते हैं"
→ "संदीप किसान क्या बताते हैं"

BAD:
"संदीप जी क्या बताते हैं"
→ "संदीप जी को क्या समस्या है"

If query is already clear:
return original query unchanged.

Return ONLY final Hindi query.
""",
            },
            {
                "role": "user",
                "content": f"""
Conversation History:

{memory_block}

Current Query:

{current_query}
""",
            },
        ]

        try:

            rewritten_query = (
                llm_service.generate(
                    messages=messages,
                    temperature=0.0,
                    max_tokens=80,
                )
            )

            rewritten_query = (
                rewritten_query.strip()
            )

            # =================================
            # SAFETY CHECKS
            # =================================

            if not rewritten_query:
                return current_query

            if (
                len(
                    rewritten_query.split()
                )
                > 25
            ):
                return current_query

            # prevent aggressive rewrites

            if (
                len(rewritten_query)
                > len(current_query) * 2
            ):
                return current_query

            logger.info(
                "Query rewritten.",
                original=current_query,
                rewritten=rewritten_query,
            )

            return rewritten_query

        except Exception as exc:

            logger.exception(
                "Query rewrite failed.",
                error=str(exc),
            )

            return current_query


query_rewrite_service = (
    QueryRewriteService()
)