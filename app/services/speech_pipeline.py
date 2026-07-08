from pathlib import Path

import os
import tempfile
import uuid

from fastapi import (
    HTTPException,
    status,
)

from app.ai.whisper_service import (
    whisper_service,
)

from app.core.logger import (
    logger,
)

from app.utils.file_utils import (
    delete_file,
)


class SpeechPipeline:

    async def process(
        self,
        audio_bytes: bytes,
    ) -> dict[str, str | float]:

        temp_path: Path | None = None

        try:

            # =================================
            # VALIDATE AUDIO
            # =================================

            if not audio_bytes:

                raise HTTPException(
                    status_code=(
                        status.HTTP_400_BAD_REQUEST
                    ),
                    detail="Empty audio file",
                )

            logger.info(
                "Audio bytes received"
            )

            # =================================
            # CREATE TEMP FILE
            # =================================

            temp_dir = tempfile.gettempdir()

            temp_filename = (
                f"{uuid.uuid4()}.wav"
            )

            temp_path = Path(
                os.path.join(
                    temp_dir,
                    temp_filename,
                )
            )

            # =================================
            # SAVE AUDIO
            # =================================

            with open(
                temp_path,
                "wb",
            ) as audio_file:

                audio_file.write(
                    audio_bytes
                )

            logger.info(
                "Temporary audio file saved",
                path=str(temp_path),
            )

            # =================================
            # TRANSCRIBE
            # =================================

            result = (
                whisper_service.transcribe(
                    temp_path
                )
            )

            logger.info(
                "Speech transcription completed"
            )

            # =================================
            # SAFE RESPONSE
            # =================================

            transcript = (
                result.get(
                    "transcript",
                    ""
                )
                or result.get(
                    "text",
                    ""
                )
            ).strip()

            language = (
                result.get(
                    "language",
                    "unknown",
                )
            )

            confidence = (
                result.get(
                    "confidence",
                    1.0,
                )
            )

            return {

                "transcript":
                    transcript,

                "language":
                    language,

                "confidence":
                    confidence,
            }

        except HTTPException:
            raise

        except Exception as exc:

            logger.exception(
                (
                    "Speech pipeline failed: "
                    f"{str(exc)}"
                )
            )

            raise HTTPException(
                status_code=(
                    status
                    .HTTP_500_INTERNAL_SERVER_ERROR
                ),
                detail=(
                    f"Transcription failed: "
                    f"{str(exc)}"
                ),
            ) from exc

        finally:

            # =================================
            # DELETE TEMP FILE
            # =================================

            if (
                temp_path is not None
                and temp_path.exists()
            ):

                delete_file(
                    temp_path
                )

                logger.info(
                    "Temporary file deleted",
                    path=str(temp_path),
                )


speech_pipeline = (
    SpeechPipeline()
)
