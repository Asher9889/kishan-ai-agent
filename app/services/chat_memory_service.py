from typing import Any

from sqlalchemy import (
    text,
)

from app.ai.llm import (
    llm_service,
)

from app.core.logger import (
    logger,
)

from app.db.mssql import (
    mssql_service,
)
from app.ai.extractor import (
    information_extractor,
)

class ChatMemoryService:

    # =====================================
    # SAVE MESSAGE
    # =====================================

    def save_message(
        self,
        *,
        thread_id: str,
        role: str,
        message: str,
    ) -> None:

        if not (
            mssql_service.is_enabled()
        ):

            return

        sql = """
        INSERT INTO chat_messages (
            thread_id,
            role,
            message
        )
        VALUES (
            :thread_id,
            :role,
            :message
        )
        """

        try:

            mssql_service.execute(
                sql=sql,
                params={
                    "thread_id": (
                        thread_id
                    ),
                    "role": role,
                    "message": message,
                },
            )

            logger.info(
                "Chat message saved.",
                thread_id=thread_id,
                role=role,
            )

        except Exception as exc:

            logger.exception(
                "Failed to save message.",
                error=str(exc),
            )

    # =====================================
    # GET RECENT MESSAGES
    # =====================================

    def get_recent_messages(
        self,
        *,
        thread_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:

        if not (
            mssql_service.is_enabled()
        ):

            return []

        sql = text(
            f"""
            SELECT TOP {limit}
                role,
                message,
                created_at
            FROM chat_messages
            WHERE thread_id = :thread_id
            ORDER BY created_at DESC
            """
        )

        try:

            rows = (
                mssql_service.fetch_all(
                    sql=sql,
                    params={
                        "thread_id": (
                            thread_id
                        )
                    },
                )
            )

            messages = []

            for row in reversed(
                rows
            ):

                messages.append(
                    {
                        "role": row[
                            "role"
                        ],
                        "message": row[
                            "message"
                        ],
                    }
                )

            logger.info(
                "Recent messages loaded.",
                thread_id=thread_id,
                count=len(messages),
            )

            return messages

        except Exception as exc:

            logger.exception(
                "Failed to load memory.",
                error=str(exc),
            )

            return []

    # =====================================
    # BUILD CONVERSATION SUMMARY
    # =====================================

    def build_summary(
        self,
        *,
        thread_id: str,
        max_messages: int = 30,
    ) -> str:

        messages = (
            self.get_recent_messages(
                thread_id=thread_id,
                limit=max_messages,
            )
        )

        if not messages:

            return ""

        formatted = []

        for msg in messages:

            formatted.append(
                f"""
{msg['role']}:
{msg['message']}
"""
            )

        conversation_text = (
            "\n".join(
                formatted
            )
        )

        messages_payload = [

            {
                "role": "system",
                "content": """
You summarize agricultural conversations.

Your goal:
preserve important context.

Keep summary short.

Include:
- crop
- symptoms
- diagnosis progress
- recommendations
- unresolved issues

Do not include unnecessary wording.
""",
            },

            {
                "role": "user",
                "content": f"""
Conversation:

{conversation_text}
""",
            },
        ]

        try:

            summary = (
                llm_service.generate(
                    messages=messages_payload,
                    temperature=0.1,
                    max_tokens=250,
                )
            )

            logger.info(
                "Conversation summary built.",
                thread_id=thread_id,
            )

            return summary.strip()

        except Exception as exc:

            logger.exception(
                "Summary generation failed.",
                error=str(exc),
            )

            return ""

    # =====================================
    # BUILD WORKING MEMORY
    # =====================================

    def build_working_memory(
        self,
        *,
        recent_messages: list[dict[str, Any]],
    ) -> dict:

        working_memory = {
            "active_crop": None,
            "active_problem": None,
            "last_user_message": None,
            "conversation_stage": "diagnosis",
        }

        crop_keywords = [

            "मक्का",
            "गेहूँ",
            "धान",
            "गन्ना",
            "चना",
            "सरसों",
            "आलू",
            "टमाटर",
            "प्याज",
            "बाजरा",

        ]

        try:

            for message in reversed(recent_messages):

                role = message.get("role")

                content = message.get(
                    "message",
                    "",
                )

                if (
                    role == "user"
                    and not working_memory["last_user_message"]
                ):
                    working_memory[
                        "last_user_message"
                    ] = content

                # ==========================
                # ACTIVE CROP
                # ==========================

                if (
                    role == "user"
                    and not working_memory["active_crop"]
                ):

                    try:

                        extracted = (
                            information_extractor.extract(
                                content
                            )
                        )

                        crop = extracted.get(
                            "crop"
                        )

                        if crop:

                            working_memory[
                                "active_crop"
                            ] = crop

                            logger.info(
                                "Crop stored in memory.",
                                crop=crop,
                            )

                    except Exception as exc:

                        logger.exception(
                            "Crop extraction failed.",
                            error=str(exc),
                        )

            logger.info(
                "Working memory built.",
                active_crop=working_memory[
                    "active_crop"
                ],
            )

            return working_memory

        except Exception as exc:

            logger.exception(
                "Working memory build failed.",
                error=str(exc),
            )

            return working_memory

chat_memory_service = (
    ChatMemoryService()
)
