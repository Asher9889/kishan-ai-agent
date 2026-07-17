import re
from typing import Iterator


class SentenceStreamer:
    """
    Production-ready incremental sentence streamer.

    Designed for:

    - LiveKit Voice Agents
    - ChatGPT Voice style streaming
    - Gemini Live style streaming
    - Streaming TTS pipelines

    Workflow

        LLM Tokens
              │
              ▼
        SentenceStreamer.push()
              │
              ▼
        Completed Sentence
              │
              ▼
        TTS Queue
              │
              ▼
        LiveKit Audio
    """

    SENTENCE_PATTERN = re.compile(
        r"[।!?]+|(?<!\d)\.(?!\d)"
    )

    def __init__(self) -> None:

        self._buffer = ""

    # =====================================================
    # PUSH NEW TEXT
    # =====================================================

    def push(
        self,
        chunk: str,
    ) -> Iterator[str]:

        """
        Feed new text into the streamer.

        Emits complete sentences immediately.
        """

        if not chunk:
            return

        self._buffer += chunk

        while True:

            match = self.SENTENCE_PATTERN.search(
                self._buffer
            )

            if match is None:
                break

            sentence_end = match.end()

            sentence = (
                self._buffer[:sentence_end]
                .strip()
            )

            self._buffer = (
                self._buffer[sentence_end:]
                .lstrip()
            )

            if sentence:

                yield sentence

    # =====================================================
    # FLUSH REMAINING BUFFER
    # =====================================================

    def flush(
        self,
    ) -> Iterator[str]:

        """
        Emit remaining incomplete sentence.

        Call once after LLM finishes.
        """

        remaining = (
            self._buffer
            .strip()
        )

        self._buffer = ""

        if remaining:

            yield remaining

    # =====================================================
    # RESET SESSION
    # =====================================================

    def reset(
        self,
    ) -> None:

        """
        Clear internal state.

        Call before starting a new conversation.
        """

        self._buffer = ""

    # =====================================================
    # HAS PENDING DATA
    # =====================================================

    def has_pending(
        self,
    ) -> bool:

        return bool(
            self._buffer.strip()
        )


sentence_streamer = SentenceStreamer()