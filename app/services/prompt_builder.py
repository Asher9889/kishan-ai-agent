from typing import Any


class PromptBuilder:

    def build(
        self,
        *,
        current_query: str,
        rag_contexts: list[
            dict[str, Any]
        ],
        memory_messages: list[
            dict[str, Any]
        ],
    ) -> list:

        # =====================================
        # FORMAT MEMORY
        # =====================================

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

        memory_block = "\n".join(
            memory_lines
        )

        if not memory_block.strip():

            memory_block = (
                "No previous conversation."
            )

        # =====================================
        # FORMAT RAG CONTEXT
        # =====================================

        rag_entries = []

        for item in rag_contexts:

            metadata = (
                item.get(
                    "metadata",
                    {},
                )
                or {}
            )

            document = item.get(
                "document",
                "",
            )

            crop = (
                metadata.get(
                    "crop"
                )
                or ""
            )

            category = (
                metadata.get(
                    "category"
                )
                or ""
            )

            problem = (
                metadata.get(
                    "problem"
                )
                or ""
            )

            summary = (
                metadata.get(
                    "summary"
                )
                or ""
            )

            rag_entries.append(
                f"""
Crop: {crop}
Category: {category}
Problem: {problem}

Summary:
{summary}

Knowledge:
{document}
"""
            )

        rag_block = "\n\n".join(
            rag_entries
        )

        if not rag_block.strip():

            rag_block = (
                "No relevant agricultural knowledge found."
            )

        # =====================================
        # SYSTEM PROMPT
        # =====================================

        system_prompt = """
You are KrishiGPT,
an intelligent agricultural assistant.

Your goal is to help farmers conversationally.

Behave naturally.

Think carefully before answering.

Ask follow-up questions only when necessary.

Avoid repetitive responses.

Avoid sounding robotic.

Avoid sounding like a survey form.

Maintain conversational continuity.

If information is incomplete,
ask the single most useful next question.

Keep responses practical,
clear,
and farmer-friendly.

Do not hallucinate.

If uncertain,
say so honestly.
"""

        # =====================================
        # BUILD CHAT MESSAGES
        # =====================================

        messages = [

            {
                "role": "system",
                "content": system_prompt,
            },

            {
                "role": "assistant",
                "content": f"""
Previous Conversation:

{memory_block}
""",
            },

            {
                "role": "assistant",
                "content": f"""
Relevant Agricultural Knowledge:

{rag_block}
""",
            },

            {
                "role": "user",
                "content": current_query,
            },
        ]

        return messages


prompt_builder = (
    PromptBuilder()
)
