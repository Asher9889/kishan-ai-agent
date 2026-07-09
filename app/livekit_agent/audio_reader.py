import asyncio
from livekit import rtc
import numpy as np
from sqlalchemy import event

class AudioReader:

    def __init__(
        self,
        participant: rtc.RemoteParticipant,
        track: rtc.Track,
        queue: asyncio.Queue,
    ):

        self.participant = participant
        self.track = track
        self.queue = queue
        self.stream: rtc.AudioStream | None = None
        self.running = False # simple flag to stop or start reading audio

    async def start(self):

        print(f"Starting audio reader for {self.participant.identity}")
        self.running = True
        self.stream = rtc.AudioStream(self.track)

        try:
            async for event in self.stream:
                if not self.running:
                    break 
                # print(f"Audio frame received from {self.participant.identity}, size: {len(event.frame.data)}, bytes, Full Event is: {event}")
                
                
                # frame = event.frame
                
                # print(type(frame.data))
                # print(frame.data.format)
                # print(frame.data.itemsize)
                # print(frame.data.shape)

                # pcm = np.asarray(frame.data)

                # print(pcm.dtype)
                # print(pcm.min())
                # print(pcm.max())
                # print(np.abs(pcm).mean())
                
                
                # print(type(event.frame))
                # print(event.frame)
                await self.queue.put(event.frame) 
                """
                each frame contains:
                AudioFrame
                ├── sample_rate = 48000
                ├── num_channels = 1
                ├── samples_per_channel = 480
                └── data = PCM samples
                """
        except Exception as exc:
            print(f"Audio reader failed: {exc}")
        finally:
            await self.stop()

    async def stop(self):
        self.running = False
        if self.stream and hasattr(self.stream,"aclose"):
            await self.stream.aclose()
        print(f"Stopped audio reader for {self.participant.identity}")