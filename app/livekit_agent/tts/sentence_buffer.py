import re


class SentenceBuffer:

    _SENTENCE_END_RE = re.compile(r"^(.*?[।.!?])(?:\s+|$)", re.DOTALL)

    def __init__(self):
        self._buffer = ""

    def push(self, token: str) -> str | None:
        self._buffer += token

        match = self._SENTENCE_END_RE.search(self._buffer)

        if match is None:
            return None

        sentence = match.group(1).strip()

        # Keep everything after the sentence for later
        self._buffer = self._buffer[match.end():]

        return sentence

    def flush(self) -> str | None:
        remaining = self._buffer.strip()

        if not remaining:
            return None

        self._buffer = ""
        return remaining