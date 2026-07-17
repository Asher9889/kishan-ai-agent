# # class VoiceFormatter:

# #     def format(
# #         self,
# #         text: str,
# #     ) -> str:

# #         return text


# # voice_formatter = VoiceFormatter()

# import re
# from app.ai.llm import llm_service



# class VoiceFormatter:
#     """
#     Production Voice Formatter

#     Optimized for:
#     - LiveKit
#     - ChatGPT Voice
#     - Gemini Live
#     """

#     MAX_SENTENCES = 3
#     MAX_WORDS = 70

#     REMOVE_ENDINGS = (
#         "क्या आपके पास",
#         "क्या आप",
#         "यदि आप",
#         "अगर आप",
#         "और जानकारी",
#         "और जानना चाहते",
#         "बताइए",
#     )

#     def format(
#         self,
#         text: str,
#     ) -> str:

#         if not text:
#             return ""

#         # =====================================
#         # Normalize whitespace
#         # =====================================

#         text = re.sub(r"\s+", " ", text).strip()

#         # =====================================
#         # Remove follow-up questions
#         # =====================================

#         sentences = re.split(r"(?<=[।.!?])\s+", text)

#         cleaned = []

#         seen = set()

#         for sentence in sentences:

#             sentence = sentence.strip()

#             if not sentence:
#                 continue

#             duplicate_key = sentence.lower()

#             if duplicate_key in seen:
#                 continue

#             seen.add(duplicate_key)

#             if any(
#                 sentence.startswith(x)
#                 for x in self.REMOVE_ENDINGS
#             ):
#                 break

#             cleaned.append(sentence)

#             if len(cleaned) >= self.MAX_SENTENCES:
#                 break

#         text = " ".join(cleaned)

#         # =====================================
#         # Limit words
#         # =====================================

#         words = text.split()

#         if len(words) > self.MAX_WORDS:

#             text = " ".join(
#                 words[: self.MAX_WORDS]
#             ).rstrip()

#             if not text.endswith(("।", ".", "!", "?")):
#                 text += "..."

#         return text.strip()


# voice_formatter = VoiceFormatter()

# =============================================================================

import re
from pathlib import Path

from app.ai.llm import llm_service
from app.core.logger import logger


class VoiceFormatter:
    """
    Production Voice Formatter with LLM-powered conversational rewrite.

    Optimized for:
    - LiveKit
    - ChatGPT Voice
    - Gemini Live

    Flow:
        1. Load system prompt from voice_prompt.txt
        2. Build messages: system + user question + factual answer
        3. Call LLM (Groq) to rewrite factually into natural conversation
        4. Apply regex cleanup (existing rules)
        5. Return polished voice‑friendly response
    """

    MAX_SENTENCES = 3
    MAX_WORDS = 70

    REMOVE_ENDINGS = (
        "क्या आपके पास",
        "क्या आप",
        "यदि आप",
        "अगर आप",
        "और जानकारी",
        "और जानना चाहते",
        "बताइए",
    )

    def __init__(self):
        self.system_prompt = self._load_prompt()

    # ----------------------------------------------------------------------
    # Prompt loading
    # ----------------------------------------------------------------------

    def _load_prompt(self) -> str:
        """Load voice_prompt.txt once at startup."""
        prompt_path = (
            Path(__file__).parent.parent
            / "prompts"
            / "voice_prompt.txt"
        )
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.exception(f"Failed to load voice_prompt.txt: {e}")
            # Fallback minimal system prompt
            return (
                "You are a friendly, conversational agricultural assistant. "
                "Rewrite the factual answer into a natural, voice‑friendly reply. "
                "Never invent facts; always stay faithful to the provided answer."
            )

    # ----------------------------------------------------------------------
    # Build messages for LLM
    # ----------------------------------------------------------------------

    def _build_messages(self, *, question: str, answer: str) -> list[dict[str, str]]:
        """Build the messages payload for llm_service.generate()."""
        return [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": (
                    f"User Question:\n{question}\n\n"
                    f"Factual Answer:\n{answer}"
                ),
            },
        ]

    # ----------------------------------------------------------------------
    # LLM rewrite with fallback
    # ----------------------------------------------------------------------

    def _rewrite_with_llm(self, *, question: str, answer: str) -> str:
        """Call LLM to rewrite the answer conversationally; fallback to original."""
        try:
            messages = self._build_messages(question=question, answer=answer)
            rewritten = llm_service.generate(
                messages=messages,
                temperature=0.4,
                max_tokens=250,
            )
            # Ensure we got a non‑empty string back
            if rewritten and isinstance(rewritten, str):
                return rewritten.strip()
            else:
                return answer
        except Exception as e:
            logger.exception(f"LLM rewrite failed, using fallback answer: {e}")
            return answer

    # ----------------------------------------------------------------------
    # Existing cleanup logic (unchanged)
    # ----------------------------------------------------------------------

    def _cleanup(self, text: str) -> str:
        """
        Apply the same production cleaning rules used before:
        - Normalise whitespace
        - Remove duplicate sentences
        - Trim follow‑up questions
        - Limit to MAX_SENTENCES and MAX_WORDS
        """
        if not text:
            return ""

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Split into sentences
        sentences = re.split(r"(?<=[।.!?])\s+", text)
        cleaned = []
        seen = set()

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Remove duplicates
            duplicate_key = sentence.lower()
            if duplicate_key in seen:
                continue
            seen.add(duplicate_key)

            # Stop at follow‑up questions
            if any(sentence.startswith(x) for x in self.REMOVE_ENDINGS):
                break

            cleaned.append(sentence)

            # Enforce sentence limit
            if len(cleaned) >= self.MAX_SENTENCES:
                break

        text = " ".join(cleaned)

        # Enforce word limit
        words = text.split()
        if len(words) > self.MAX_WORDS:
            text = " ".join(words[:self.MAX_WORDS]).rstrip()
            if not text.endswith(("।", ".", "!", "?")):
                text += "..."

        return text.strip()

    # ----------------------------------------------------------------------
    # Public interface – called by ask_v4.py
    # ----------------------------------------------------------------------

    def format(
        self,
        *,
        question: str,
        answer: str,
        thread_id: str | None = None,   # reserved for future memory use
    ) -> str:
        """
        Main entry point.

        Args:
            question: The user's original question.
            answer:  The factual answer from orchestrator / RAG / SQL.
            thread_id: (optional) for future conversation‑aware rewrite.

        Returns:
            Conversational, voice‑optimised reply.
        """
        # 1. Rewrite with LLM
        rewritten = self._rewrite_with_llm(question=question, answer=answer)

        # 2. Apply existing cleanup (sentence/word limits, duplicates, etc.)
        return self._cleanup(rewritten)


# Singleton instance – keep the same global name used in ask_v4.py
voice_formatter = VoiceFormatter()