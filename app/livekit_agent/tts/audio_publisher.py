from livekit import rtc


class AudioPublisher:

    def __init__(self, audio_source: rtc.AudioSource):
        self.audio_source = audio_source

    async def publish(self, frame: rtc.AudioFrame):
        await self.audio_source.capture_frame(frame)

    async def wait_for_playout(self):
        await self.audio_source.wait_for_playout()

    def clear(self):
        self.audio_source.clear_queue()