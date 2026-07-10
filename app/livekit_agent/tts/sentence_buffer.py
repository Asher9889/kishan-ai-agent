class SentenceBuffer:

    def __init__(self):
        self._buffer = ""
        
    def push(self, token: str) -> str | None:
        self._buffer += token

        if self._buffer.endswith(("।", ".", "!", "?")):
            sentence = self._buffer.strip()
            self._buffer = ""
            return sentence

        return None

    def flush(self) -> str | None:
        if not self._buffer.strip():
            return None

        sentence = self._buffer.strip()
        self._buffer = ""
        return sentence