class AudioChunker:

    def __init__(
        self,
        frame_duration_ms: int = 20,
        sample_rate: int = 44100,
        channels: int = 1,
        bytes_per_sample: int = 2,
    ):

        self.frame_size = (
            sample_rate
            * frame_duration_ms
            // 1000
            * channels
            * bytes_per_sample
        )

        self.buffer = bytearray()

    def push(self, pcm: bytes):

        self.buffer.extend(pcm)

        while len(self.buffer) >= self.frame_size:

            frame = bytes(
                self.buffer[: self.frame_size]
            )

            del self.buffer[: self.frame_size]

            yield frame

    def flush(self):

        if not self.buffer:
            return None

        frame = bytes(self.buffer)

        self.buffer.clear()

        return frame