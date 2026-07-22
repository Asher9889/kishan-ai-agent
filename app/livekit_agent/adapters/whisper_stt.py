from __future__ import annotations

import httpx
import wave
import os
from datetime import datetime
from livekit import rtc
from livekit.agents import stt, utils
from livekit.agents._exceptions import (
    APIConnectionError,
    APITimeoutError,
    create_api_error_from_http,
)
from livekit.agents.types import NOT_GIVEN, NotGivenOr, APIConnectOptions
from app.core.config import settings

AUDIO_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "audio_dumps")


class WhisperSTT(stt.STT):
    def __init__(
        self,
        *,
        endpoint_url: str = "http://localhost:8000/transcribe-pcm",
        http_timeout: float = 30.0,
    ) -> None:
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=False,
                interim_results=False,
                offline_recognize=True,
            )
        )
        self._endpoint_url = endpoint_url
        self._client = httpx.AsyncClient(timeout=http_timeout)

    @property
    def model(self) -> str:
        return "faster-whisper"

    @property
    def provider(self) -> str:
        return "krishi-local"

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: NotGivenOr[str] = NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        frames = [buffer] if isinstance(buffer, rtc.AudioFrame) else buffer
        if not frames:
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                request_id=utils.shortuuid("stt_"),
                alternatives=[],
            )

        merged = utils.merge_frames(frames)
        pcm_bytes = (
            merged.data.tobytes()
            if hasattr(merged.data, "tobytes")
            else bytes(merged.data)
        )

        if settings.WHISPER_AUDIO_DUMP:
            self._save_audio_dump(pcm_bytes, merged.sample_rate)

        headers = {
            "X-Sample-Rate": str(merged.sample_rate),
        }

        try:
            response = await self._client.post(
                self._endpoint_url,
                content=pcm_bytes,
                headers=headers,
            )
        except httpx.TimeoutException as e:
            raise APITimeoutError(
                f"Whisper STT request timed out: {e}"
            ) from e
        except httpx.ConnectError as e:
            raise APIConnectionError(
                f"Failed to connect to Whisper STT at {self._endpoint_url}: {e}"
            ) from e
        except httpx.HTTPError as e:
            raise APIConnectionError(
                f"Whisper STT request failed: {e}"
            ) from e

        if response.status_code != 200:
            raise create_api_error_from_http(
                message="Whisper STT transcription failed",
                status=response.status_code,
                body=response.text,
            )

        try:
            payload = response.json()
        except Exception as e:
            raise APIConnectionError(
                f"Failed to parse Whisper STT response: {e}"
            ) from e

        data = payload.get("data", {})
        transcript = (data.get("transcript", "") or "").strip()

        if not transcript:
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                request_id=utils.shortuuid("stt_"),
                alternatives=[],
            )

        confidence = float(data.get("confidence", 0.0))
        detected_language = data.get("language", "hi")

        speech_data = stt.SpeechData(
            language=detected_language,
            text=transcript,
            confidence=confidence,
        )

        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            request_id=utils.shortuuid("stt_"),
            alternatives=[speech_data],
        )

    def _save_audio_dump(self, pcm_bytes: bytes, sample_rate: int) -> None:
        try:
            os.makedirs(AUDIO_DUMP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"whisper_input_{timestamp}.wav"
            filepath = os.path.join(AUDIO_DUMP_DIR, filename)

            with wave.open(filepath, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(pcm_bytes)

            duration = len(pcm_bytes) / (2 * sample_rate)
            print(f"[AudioDump] Saved {filepath} ({duration:.2f}s, {sample_rate}Hz)")
        except Exception as e:
            print(f"[AudioDump] Failed to save audio: {e}")

    async def aclose(self) -> None:
        await self._client.aclose()
