import asyncio

from livekit import rtc

from app.livekit_agent.tts.tts_client import TTSClient
from app.livekit_agent.tts.audio_chunker import AudioChunker
from app.livekit_agent.tts.audio_publisher import AudioPublisher

class TTSPipeline:

    def __init__(self):
        self.client = TTSClient()
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.worker_task: asyncio.Task | None = None
        self.chunker = AudioChunker()
        self.resampler = rtc.AudioResampler(
            input_rate=44100,
            output_rate=48000,
            num_channels=1,
        )
        self._publisher: AudioPublisher | None = None
        
        self.on_started = None # for knowing when the TTS starts processing a sentence
        self.on_finished = None # for knowing when the TTS finishes processing a sentence

    def set_publisher(self, publisher: AudioPublisher) -> None:
        self._publisher = publisher

    async def start(self):
        if self.worker_task is None:
            self.worker_task = asyncio.create_task(self._worker())

    async def enqueue(self, sentence: str):
        await self.queue.put(sentence)

    async def _publish_frame(self, frame: rtc.AudioFrame) -> None:
        if self._publisher is None:
            raise RuntimeError(
                "TTSPipeline: AudioPublisher not set. "
                "Call set_publisher() before enqueuing sentences."
            )
        await self._publisher.publish(frame)

    async def _worker(self):
        while True:
            sentence = await self.queue.get()
            
            if self.on_started:
                self.on_started()
                
            print(f"\nStarting TTS: {sentence}")
            try:
                async for pcm in self.client.stream(sentence):
                    for chunk in self.chunker.push(pcm):
                        for frame in self.resampler.push(bytearray(chunk)):
                            await self._publish_frame(frame)

                remaining = self.chunker.flush()
                if remaining:
                    for frame in self.resampler.push(bytearray(remaining)):
                        await self._publish_frame(frame)
                for frame in self.resampler.flush():
                    await self._publish_frame(frame)
                    
                await self._publisher.wait_for_playout()

                if self.on_finished:
                    self.on_finished()

            except Exception as exc:
                print("TTS failed:", exc)
            finally:
                self.queue.task_done()

    async def close(self):
        if self.worker_task:
            self.worker_task.cancel()
        await self.client.close()