import asyncio
# from app.ai.whisper_service import whisper_service
# from app.ai.whisper_service import get_whisper_service
from livekit import rtc
from array import array
import numpy as np
import httpx
from scipy.signal import resample_poly


from app.livekit_agent.vad import SileroVAD



class SpeechPipeline:

    def __init__(self, queue: asyncio.Queue[rtc.AudioFrame]):
        self.queue = queue
        # Stores AudioFrames temporarily
        # self.frames: list[rtc.AudioFrame] = []
        self.running = False
        self.pcm_buffer = array("h") #"h" means signed 16-bit integers,
        
        
        self.vad_buffer = array("h")          # Sliding analysis window (~300 ms)
        self.speech_buffer = array("h")  
        
        self.is_speaking = False
        self.silence_frames = 0
        self.vad = SileroVAD()
        
        self.client = httpx.AsyncClient(
            base_url="http://localhost:8000",
            timeout=30.0,
        )
        # self.whisper = get_whisper_service()
        

        """_summary_
        while running
        receive 10ms frame
        append frame to vad_buffer
        append frame to speech_buffer (only if user is speaking)
        if vad_buffer has 300ms
            run Silero
            if speech
                user started talking?
                    yes -> just continue
                    no -> mark speaking=True
                reset silence counter
            else
                if speaking
                    increase silence counter
                    enough silence?
                        send speech_buffer to Whisper
                        clear speech_buffer
                        speaking=False
                discard oldest samples from vad_buffer
        """
    async def start(self):
        print("SpeechPipeline started", id(self))
        # print("Speech Pipeline Started")
        self.running = True
        
        while self.running:

            # Wait until AudioReader puts a frame
            frame = await self.queue.get()
            
            vad_samples = int(frame.sample_rate * 0.3)
            
            self.vad_buffer.extend(frame.data)
            self.pcm_buffer.extend(frame.data)

            # Approximately 1 second
            if len(self.vad_buffer) < vad_samples:
                continue
            
            audio = np.array(
                self.vad_buffer,
                dtype=np.float32,
            )
            
            audio /= 32768.0
            audio = resample_poly(
                audio,
                up=16000,
                down=48000,
            )
            
            # print("Audio length send to vad",len(audio))
            
            # print("dtype:", audio.dtype)
            # print("shape:", audio.shape)
            # print("min:", audio.min())
            # print("max:", audio.max())
            # print("mean abs:", np.abs(audio).mean())
            # print("rms:", np.sqrt(np.mean(audio ** 2)))
            
            speech_detected = self.vad.is_speech(
                audio,
                sample_rate=16000,
            )
            
            # keep only latest 300 ms
            if len(self.vad_buffer) > vad_samples:
                del self.vad_buffer[:-vad_samples]

            
            print(speech_detected)

                # Hand the current chunk to Whisper
                
                # pcm_chunk = self.pcm_buffer
                # self.pcm_buffer = array("h")  # replace the buffer with a new empty array for the next chunk
                
                # print(len(pcm_chunk), id(pcm_chunk), id(self.pcm_buffer))

                # # Immediately start collecting the next chunk
                # # self.pcm_buffer = array("h")

                # print(f"Collected {len(pcm_chunk)} PCM samples")
                
                # response = await self.client.post(
                #     "/transcribe-pcm",
                #     content=pcm_chunk.tobytes(),
                #     headers={
                #         "Content-Type": "application/octet-stream",
                #         "X-Sample-Rate": str(frame.sample_rate),
                #     },
                # )

                # result = self.whisper.transcribe_pcm(
                #     pcm_chunk,
                #     sample_rate=frame.sample_rate,
                # )

                # print(response)


    async def stop(self):
        self.running = False
        self.pcm_buffer = array("h")
        print("Speech Pipeline Stopped")