import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import settings
from app.core.logger import logger
import numpy as np
from scipy import signal


class WhisperService:
    def __init__(self) -> None:
        # logger.info(
        #     "Loading Whisper model",
        #     model=settings.WHISPER_MODEL,
        # )

        self.model = WhisperModel(
            settings.WHISPER_MODEL,
            device="cuda", # cpu for cpu
            compute_type="float16", # int8 for cpu
            local_files_only=False
        )

        logger.info(
            "Whisper model loaded",
            model=settings.WHISPER_MODEL,
        )

    def transcribe(self, audio_path: str | Path) -> dict[str, str | float]:
        segments, info = self.model.transcribe(
            str(audio_path),
            language="hi",
            beam_size=5,
            vad_filter=True,
        )

        transcript = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()

        confidence = round(float(info.language_probability), 4)

        logger.info(
            "Transcription completed",
            language=info.language,
            confidence=confidence,
        )

        return {
            "transcript": transcript,
            "language": info.language,
            "confidence": confidence,
        }
    
    def transcribe_pcm(self, pcm_buffer, sample_rate: int = 48000) -> dict[str, str | float]:
        # Convert int16 PCM to float32
        audio = np.array(
            pcm_buffer,
            dtype=np.float32, 
        )

        # Whisper expects values between -1.0 and 1.0
        audio /= 32768.0
        
           # Whisper works at 16kHz — resample from source rate (e.g. 48kHz)
        if sample_rate != 16000:
            audio = signal.resample_poly(audio, up=16000, down=sample_rate)


        segments, info = self.model.transcribe(
            audio,
            language="hi",
            beam_size=10, # quality vs speed trade-off
            vad_filter=True,  # Disable VAD filtering for PCM input
        )

        segment_list = list(segments)
        transcript = " ".join(
            seg.text.strip()
            for seg in segment_list
            if seg.text.strip()
        ).strip()

        if segment_list:
            avg_lp = sum(seg.avg_logprob for seg in segment_list) / len(segment_list)
            confidence = round(float(np.exp(avg_lp)), 4)
        else:
            confidence = 0.0

        logger.info(
            "PCM transcription completed",
            language=info.language,
            confidence=confidence,
        )

        return {
            "transcript": transcript,
            "language": info.language,
            "confidence": confidence,
        }


# Global singleton instance
# whisper_service = WhisperService()

_whisper_service: WhisperService | None = None


def get_whisper_service() -> WhisperService:
    global _whisper_service

    if _whisper_service is None:
        _whisper_service = WhisperService()

    return _whisper_service