import asyncio

from app.livekit_agent.tts.tts_client import TTSClient
from app.livekit_agent.tts.audio_chunker import AudioChunker
from app.livekit_agent.tts.audio_publisher import AudioPublisher

class TTSPipeline:

    def __init__(self,  publisher: AudioPublisher):
        self.client = TTSClient()
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.worker_task: asyncio.Task | None = None
        self.chunker = AudioChunker()
        self.publisher = publisher

    async def start(self):
        if self.worker_task is None:
            self.worker_task = asyncio.create_task(self._worker())

    async def enqueue(self, sentence: str):
        await self.queue.put(sentence)

    async def _worker(self):
        while True:
            sentence = await self.queue.get()
            print(f"\nStarting TTS: {sentence}")
            try:
                async for pcm in self.client.stream(sentence):
                    for frame in self.chunker.push(pcm):
                        print(f"Frame ready: {len(frame)} bytes")
                    # print(f"Received PCM chunk: {len(pcm)} bytes")
            except Exception as exc:
                print("TTS failed:", exc)
            finally:
                self.queue.task_done()

    async def close(self):
        if self.worker_task:
            self.worker_task.cancel()
        await self.client.close()