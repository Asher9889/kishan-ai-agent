from typing import Any

from app.ai.llm import (
    llm_service,
)

from app.core.logger import (
    logger,
)


class ConversationResponseService:

    # =====================================
    # FORMAT MEMORY
    # =====================================

    def format_memory(
        self,
        messages: list[
            dict[str, Any]
        ],
    ) -> str:

        if not messages:

            return (
                "No previous conversation."
            )

        formatted = []

        for msg in messages:

            role = msg.get(
                "role",
                "user",
            )

            content = msg.get(
                "message",
                "",
            )

            formatted.append(
                f"{role}: {content}"
            )

        return "\n".join(
            formatted
        )

    # =====================================
    # FORMAT KNOWLEDGE
    # =====================================

    def format_knowledge(
        self,
        retrieval_results: list[
            dict[str, Any]
        ],
    ) -> str:

        if not retrieval_results:

            return (
                "No external agricultural knowledge available."
            )

        blocks = []

        top_result = (
        retrieval_results[0]
        if retrieval_results
        else None
    )

        for item in retrieval_results:
            is_top_result = (
                item == top_result
                )

            metadata = (
                item.get(
                    "metadata",
                    {},
                )
                or {}
            )

            document = (
                item.get(
                    "document",
                    "",
                )
            )

            crop = metadata.get(
                "crop",
                "",
            )

            problem = metadata.get(
                "problem",
                "",
            )

            farmer_name = metadata.get(
                "farmer_name",
                "",
            )

            location = metadata.get(
                "location",
                "",
            )

            district = metadata.get(
                "district",
                "",
            )

            state = metadata.get(
                "state",
                "",
            )

            solution = metadata.get(
                "solution",
                "",
            )

            summary = metadata.get(
                "summary",
                "",
            )

            trust_score = (
                metadata.get(
                    "trust_score",
                    0,
                )
                or 0
            )

            ranking_score = (
                item.get(
                    "ranking_score",
                    0,
                )
                or 0
            )

            # =================================
            # HIGH CONFIDENCE KB
            # =================================

            if (
            ranking_score >= 0.50
            and trust_score >= 0.85
            ):

                if is_top_result:

                    section_title = (
                        "[PRIMARY GROUNDED ANSWER]"
                    )

                else:

                    section_title = (
                        "[Reliable Field Experience]"
                    )

                blocks.append(
                    f"""
            {section_title}

            Farmer Name:
            {farmer_name}

            Location:
            {location}, {district}, {state}

            Crop:
            {crop}

            Problem:
            {problem}

            Recommended Solution:
            {solution}

            IMPORTANT:
            This is grounded agricultural knowledge.
            Prefer this solution in the response.

            Field Summary:
            {summary}

            Knowledge:
            {document}
            """
                
                    )

            # =================================
            # NORMAL KNOWLEDGE
            # =================================

            else:

                blocks.append(
                    f"""
[Agricultural Knowledge]

Crop:
{crop}

Problem:
{problem}

Knowledge:
{document}
"""
                )

        return "\n\n".join(
            blocks
        )

    # =====================================
    # BUILD MESSAGES
    # =====================================

    def build_messages(
        self,
        *,
        current_query: str,
        memory_messages: list,
        retrieval_results: list,
        plan: dict,
    ) -> list:

        formatted_memory = (
            self.format_memory(
                memory_messages
            )
        )

        formatted_knowledge = (
            self.format_knowledge(
                retrieval_results
            )
        )

        # =====================================
        # SYSTEM PROMPT
        # =====================================

        system_prompt = """
You are KrishiGPT,
an intelligent agricultural assistant.

You are a conversational agricultural assistant
that prioritizes grounded farmer knowledge
and practical field experiences.

NOT:
- FAQ bot
- article writer
- robotic chatbot

Your goal:
understand the farmer naturally.

Think conversationally.

Ask follow-up questions only when necessary.

Do not sound repetitive.

Do not dump generic agricultural advice.

Keep responses:
- practical
- natural
- human-like
- context-aware

If uncertain:
say so honestly.

If ambiguity exists:
ask ONLY the most useful next question.

Use retrieved agricultural knowledge naturally when relevant.

If retrieved knowledge contains a clear treatment,
farmer experience, or practical solution:

- mention it naturally in the response
- prioritize grounded field knowledge
- avoid contradicting retrieved information
- avoid introducing unrelated medicines
  or treatments not supported by context

You may ask natural follow-up questions
if they genuinely help understand
the farmer's situation better.

If retrieved knowledge contains reliable field experiences,
you SHOULD naturally mention:

- farmer names
- farmer experiences
- district/location
- successful treatments
- practical outcomes

when they help make the answer more practical and trustworthy.

Use farmer names only occasionally and naturally,
not in every response.

Do NOT fabricate stories.

Do NOT invent names or locations.

If retrieval confidence is weak,
respond normally without forcing source attribution.

When retrieval confidence is high,
respond like an experienced agricultural advisor
sharing real grounded field knowledge naturally.
"""

        mode = (
            plan.get(
                "mode",
                "answer",
            )
        )

        planner_instruction = ""

        # =====================================
        # CLARIFICATION
        # =====================================

        if mode == (
            "clarification"
        ):

            planner_instruction = """
The query lacks important information.

Your goal:
ask ONE smart follow-up question.

Do NOT ask multiple questions.

Do NOT give treatment yet.
"""

        # =====================================
        # EXPLORE
        # =====================================

        elif mode == (
            "explore"
        ):

            planner_instruction = """
The issue is somewhat ambiguous.

Briefly explain likely possibilities.

Then ask ONE useful narrowing question.
"""

        # =====================================
        # DIAGNOSTIC
        # =====================================

        elif mode == (
            "diagnostic"
        ):

            planner_instruction = """
        Use conversational diagnostic reasoning.

        If retrieved knowledge already contains
        a direct treatment or solution:

        - mention that solution FIRST
        - do NOT replace it
        - do NOT contradict it
        - do NOT invent new medicines,
        fungicides, pesticides, or chemicals

        If needed,
        ask ONE additional clarifying question.

        Clarifying questions should ONLY:
        - understand severity
        - understand spread
        - understand timing
        - understand previous actions

        Do not override grounded knowledge.
        """

        # =====================================
        # DIRECT ANSWER
        # =====================================

        else:

            planner_instruction = """
Provide a practical direct answer.

Keep response concise and useful.
"""

        messages = [

            {
                "role": "system",
                "content": system_prompt,
            },

            {
                "role": "assistant",
                "content": f"""
Conversation History:

{formatted_memory}
""",
            },

            {
                "role": "assistant",
                "content": f"""
Relevant Agricultural Knowledge:

{formatted_knowledge}
""",
            },

            {
                "role": "assistant",
                "content": f"""
Conversation Strategy:

{planner_instruction}
""",
            },

            {
                "role": "user",
                "content": current_query,
            },
        ]

        return messages

    # =====================================
    # STREAM RESPONSE
    # =====================================

    def stream_response(
        self,
        *,
        current_query: str,
        memory_messages: list,
        retrieval_results: list,
        plan: dict,
    ):

        messages = (
            self.build_messages(
                current_query=current_query,
                memory_messages=(
                    memory_messages
                ),
                retrieval_results=(
                    retrieval_results
                ),
                plan=plan,
            )
        )

        logger.info(
            "Conversation messages built."
        )

        return (
            llm_service.stream_generate(
                messages=messages,
                temperature=0.2,
                max_tokens=500,
            )
        )


conversation_response_service = (
    ConversationResponseService()
)
