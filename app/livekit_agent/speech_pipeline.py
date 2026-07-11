import asyncio
# from app.ai.whisper_service import whisper_service
# from app.ai.whisper_service import get_whisper_service
from livekit import rtc
from array import array
import numpy as np
import httpx
from scipy.signal import resample_poly


from app.livekit_agent.conversation_pipeline import ConversationPipeline
from app.livekit_agent.vad import SileroVAD



class SpeechPipeline:

    def __init__(self, queue: asyncio.Queue[rtc.AudioFrame], conversation_pipeline: ConversationPipeline):
        self.queue = queue
        self.listening = True
        self.conversation_pipeline = conversation_pipeline
        # Stores AudioFrames temporarily
        # self.frames: list[rtc.AudioFrame] = []
        self.running = False
        
        self.vad_buffer = array("h")   # For Silero Sliding analysis window 
        self.pre_roll_buffer = array("h")  # Last 300 ms
        self.speech_buffer = array("h")  # Whole utterance
        
        self.is_speaking = False
        self.silence_frames = 0
        self.vad = SileroVAD()
        
        self.vad_window_ms = 300
        self.silence_timeout_ms = 2000  # 2 seconds of silence to consider speech ended
        # 10 ms per LiveKit frame
        self.frame_duration_ms = 10
        
        self.silence_frames = 0
        self.speech_hits = 0

        
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
        self.running = True

        while self.running:
            """
            at every iternation we get 10ms data more.
            for 48000 hz 10 ms = 480 samples
            for 16000 hz 10 ms = 160 samples
            """

            # Wait for next 10 ms frame
            frame = await self.queue.get()
            
            # Ignore microphone while AI is speaking
            if not self.listening:
                continue

            # Buffer sizes
            vad_samples = int(frame.sample_rate * 0.3)       # 300 ms
            pre_roll_samples = int(frame.sample_rate * 0.3)  # 300 ms

            # Update buffers
            self.vad_buffer.extend(frame.data)  # adding more 10ms sample which is 480 sample
            self.pre_roll_buffer.extend(frame.data) # adding more 10ms sample which is 480 sample

            # Keep only the latest 300 ms in pre-roll
            if len(self.pre_roll_buffer) > pre_roll_samples:
                del self.pre_roll_buffer[:-pre_roll_samples] # delete first 10ms sample

            # Wait until we have enough audio for VAD
            if len(self.vad_buffer) < vad_samples: # it means we do not have 300 ms sample to start pipeline
                continue

            # Prepare audio for Silero
            audio = np.array(
                self.vad_buffer,
                dtype=np.float32,
            )

            audio /= 32768.0

            audio = resample_poly(
                audio,
                up=16000,
                down=frame.sample_rate,
            )

            # Run VAD
            speech_detected = self.vad.is_speech(
                audio,
                sample_rate=16000,
            )

            # Keep only the latest 300 ms in VAD buffer
            if len(self.vad_buffer) > vad_samples:
                del self.vad_buffer[:-vad_samples]

            # Speech detected
            if speech_detected:
                self.speech_hits += 1

                if not self.is_speaking and self.speech_hits >= 2:

                    print("Speech started")

                    self.is_speaking = True
                    self.silence_frames = 0

                    # Start the utterance with the previous 300 ms
                    self.speech_buffer = array("h")
                    self.speech_buffer.extend(self.pre_roll_buffer)

                # Add current frame
                self.speech_buffer.extend(frame.data)

                # Reset silence counter
                self.silence_frames = 0

            # ==========================================================
            # Silence detected
            # ==========================================================
            else:
                self.speech_hits = 0
                if self.is_speaking:

                    # Keep trailing silence
                    self.speech_buffer.extend(frame.data)

                    self.silence_frames += 1

                    if self.silence_frames >= (self.silence_timeout_ms // self.frame_duration_ms):

                        print("Speech ended")

                        pcm_chunk = self.speech_buffer

                        # Reset state for next utterance
                        self.speech_buffer = array("h")
                        self.is_speaking = False
                        self.silence_frames = 0

                        print(f"Sending {len(pcm_chunk)} PCM samples to Whisper")
                        
                        duration_ms = (len(pcm_chunk) / frame.sample_rate) * 1000
                        if duration_ms < 700:
                            print(f"Ignoring short utterance: {duration_ms:.0f} ms")
                            continue
                        
                        await self.conversation_pipeline.process_pcm(pcm_chunk, frame.sample_rate)
    
    async def stop(self):
        self.running = False
        self.pcm_buffer = array("h")
        print("Speech Pipeline Stopped")
        
    def pause(self):
        print("SpeechPipeline paused")
        self.listening = False
        self.vad_buffer = array("h")
        self.pre_roll_buffer = array("h")
        self.speech_buffer = array("h")

        self.is_speaking = False
        self.silence_frames = 0

    def resume(self):
        print("SpeechPipeline resumed")
        self.listening = True
    
        
        
        
        