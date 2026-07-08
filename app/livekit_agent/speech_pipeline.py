import asyncio
from app.ai.whisper_service import whisper_service
from livekit import rtc
from array import array
import numpy as np

class SpeechPipeline:

    def __init__(self, queue: asyncio.Queue[rtc.AudioFrame]):
        self.queue = queue
        # Stores AudioFrames temporarily
        # self.frames: list[rtc.AudioFrame] = []
        self.running = False
        self.pcm_buffer = array("h") #"h" means signed 16-bit integers,
        

    async def start(self):
        print("Speech Pipeline Started")
        self.running = True
        while self.running:

            # Wait until AudioReader puts a frame
            frame = await self.queue.get()

            # self.frames.append(frame)
            self.pcm_buffer.extend(frame.data)
            # print(type(frame.data))
            # print(frame.data.format)
            # print(frame.data.itemsize)
            # print(frame.data.shape)
            # print(frame.data.nbytes)

            # Approximately 1 second
            if len(self.pcm_buffer) >= frame.sample_rate:

                # Hand the current chunk to Whisper
                pcm_chunk = self.pcm_buffer

                # Immediately start collecting the next chunk
                self.pcm_buffer = array("h")

                print(f"Collected {len(pcm_chunk)} PCM samples")

                result = whisper_service.transcribe_pcm(
                    pcm_chunk,
                    sample_rate=frame.sample_rate,
                )

                print(result)


    async def stop(self):
        self.running = False
        self.pcm_buffer = array("h")
        print("Speech Pipeline Stopped")