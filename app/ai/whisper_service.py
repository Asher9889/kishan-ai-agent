import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

from pathlib import Path

from faster_whisper import WhisperModel

from app.core.config import settings
from app.core.logger import logger
import numpy as np


class WhisperService:
    def __init__(self) -> None:
        logger.info(
            "Loading Whisper model",
            model=settings.WHISPER_MODEL,
        )

        self.model = WhisperModel(
            settings.WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
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

        segments, info = self.model.transcribe(
            audio,
            language="hi",
            beam_size=5,
            vad_filter=False,  # Disable VAD filtering for PCM input
        )

        transcript = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()

        confidence = round(
            float(info.language_probability),
            4,
        )

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
whisper_service = WhisperService()