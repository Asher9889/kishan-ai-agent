from pathlib import Path
from uuid import uuid4

import aiofiles
from fastapi import UploadFile

from app.core.config import settings


ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm",".mp4"}


def validate_file_extension(filename: str) -> None:
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )


async def validate_file_size(file: UploadFile) -> None:
    content = await file.read()

    max_size_bytes = settings.MAX_AUDIO_MB * 1024 * 1024

    if len(content) > max_size_bytes:
        raise ValueError(
            f"File size exceeds {settings.MAX_AUDIO_MB} MB limit"
        )

    await file.seek(0)


async def save_upload_file(file: UploadFile) -> Path:
    temp_dir = Path(settings.TEMP_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(file.filename or "audio.wav").suffix.lower()
    temp_path = temp_dir / f"{uuid4()}{extension}"

    async with aiofiles.open(temp_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    await file.seek(0)

    return temp_path


def delete_file(path: Path) -> None:
    if path.exists():
        path.unlink()