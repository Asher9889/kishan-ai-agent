from pathlib import Path
from typing import Any


class VoicePromptBuilder:

    def __init__(self) -> None:

        prompt_file = (
            Path(__file__)
            .resolve()
            .parent.parent
            / "prompts"
            / "voice_prompts.txt"
        )

        self.system_prompt = (
            prompt_file.read_text(
                encoding="utf-8"
            ).strip()
        )

    # =====================================================
    # BUILD VOICE PROMPT
    # =====================================================

    def build(
        self,
        *,
        current_query: str,
        rag_contexts: list[dict[str, Any]],
        memory_messages: list[dict[str, Any]],
        plan: dict,
    ) -> list[dict[str, str]]:

        # =================================================
        # FORMAT MEMORY
        # =================================================

        memory_lines: list[str] = []

        for message in memory_messages:

            role = message.get(
                "role",
                "user",
            )

            content = message.get(
                "message",
                "",
            ).strip()

            if content:

                memory_lines.append(
                    f"{role}: {content}"
                )

        memory_block = "\n".join(
            memory_lines
        )

        if not memory_block:

            memory_block = (
                "No previous conversation."
            )

        # =================================================
        # FORMAT RAG CONTEXT
        # =================================================

        rag_entries: list[str] = []

        for item in rag_contexts:

            metadata = (
                item.get(
                    "metadata",
                    {},
                )
                or {}
            )

            rag_entries.append(
                f"""
Crop: {metadata.get("crop", "")}

Category: {metadata.get("category", "")}

Problem: {metadata.get("problem", "")}

Summary:
{metadata.get("summary", "")}

Knowledge:
{item.get("document", "")}
""".strip()
            )

        rag_block = "\n\n".join(
            rag_entries
        )

        if not rag_block:

            rag_block = (
                "No relevant agricultural knowledge available."
            )

        # =================================================
        # CONVERSATION STRATEGY
        # =================================================

        mode = (
            plan.get(
                "mode",
                "answer",
            )
        )

        planner_instruction = ""

        if mode == "clarification":

            planner_instruction = """
The farmer has not provided enough information.

Ask ONLY ONE follow-up question.

Do not provide treatment yet.

Do not ask multiple questions.
"""

        elif mode == "diagnostic":

            planner_instruction = """
Think like an agricultural expert.

Give the most likely explanation first.

Then ask ONLY ONE diagnostic question.

Do not overwhelm the farmer.

Do not jump directly to pesticides.
"""

        elif mode == "explore":

            planner_instruction = """
Briefly explain the most likely possibilities.

Then ask ONE useful follow-up question
to narrow the diagnosis.
"""

        else:

            planner_instruction = """
Answer directly.

Keep it short.

Maximum 3 sentences.

If more information is needed,
ask only one follow-up question.
"""

        # =================================================
        # BUILD CHAT MESSAGES
        # =================================================

        messages = [

            {
                "role": "system",
                "content": self.system_prompt,
            },

            {
                "role": "assistant",
                "content": f"""
Conversation Memory

{memory_block}
""".strip(),
            },

            {
                "role": "assistant",
                "content": f"""
Relevant Agricultural Knowledge

{rag_block}
""".strip(),
            },

            {
                "role": "assistant",
                "content": f"""
Conversation Strategy

{planner_instruction}
""".strip(),
            },

            {
                "role": "assistant",
                "content": """
IMPORTANT

The farmer is talking over voice.

Keep every response conversational.

Answer only what the farmer asked.

Do not generate articles.

Do not repeat information.

Maximum 3 short sentences.

Maximum 60 words.

Speak naturally.

If required,
ask only ONE follow-up question.
""".strip(),
            },

            {
                "role": "user",
                "content": current_query.strip(),
            },

        ]

        return messages


voice_prompt_builder = VoicePromptBuilder()