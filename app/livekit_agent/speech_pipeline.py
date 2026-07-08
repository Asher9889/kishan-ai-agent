import asyncio
# from app.ai.whisper_service import whisper_service
# from app.ai.whisper_service import get_whisper_service
from livekit import rtc
from array import array
import numpy as np
import httpx



class SpeechPipeline:

    def __init__(self, queue: asyncio.Queue[rtc.AudioFrame]):
        self.queue = queue
        # Stores AudioFrames temporarily
        # self.frames: list[rtc.AudioFrame] = []
        self.running = False
        self.pcm_buffer = array("h") #"h" means signed 16-bit integers,
        self.client = httpx.AsyncClient(
            base_url="http://localhost:8000",
            timeout=30.0,
        )
        # self.whisper = get_whisper_service()
        

    async def start(self):
        print("SpeechPipeline started", id(self))
        # print("Speech Pipeline Started")
        self.running = True
        while self.running:

            # Wait until AudioReader puts a frame
            frame = await self.queue.get()

            self.pcm_buffer.extend(frame.data)

            # Approximately 1 second
            if len(self.pcm_buffer) >= frame.sample_rate:

                # Hand the current chunk to Whisper
                
                pcm_chunk = self.pcm_buffer
                self.pcm_buffer = array("h")  # replace the buffer with a new empty array for the next chunk
                
                print(len(pcm_chunk), id(pcm_chunk), id(self.pcm_buffer))

                # Immediately start collecting the next chunk
                # self.pcm_buffer = array("h")

                print(f"Collected {len(pcm_chunk)} PCM samples")
                
                response = await self.client.post(
                    "/transcribe-pcm",
                    content=pcm_chunk.tobytes(),
                    headers={
                        "Content-Type": "application/octet-stream",
                        "X-Sample-Rate": str(frame.sample_rate),
                    },
                )

                # result = self.whisper.transcribe_pcm(
                #     pcm_chunk,
                #     sample_rate=frame.sample_rate,
                # )

                print(response)


    async def stop(self):
        self.running = False
        self.pcm_buffer = array("h")
        print("Speech Pipeline Stopped")