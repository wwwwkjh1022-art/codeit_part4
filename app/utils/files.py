import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.config import Settings


def save_upload_file(upload: UploadFile | None, settings: Settings) -> str | None:
    if upload is None or not upload.filename:
        return None

    suffix = Path(upload.filename).suffix.lower()
    if suffix not in settings.allowed_image_extensions:
        raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다.")

    destination = settings.upload_dir / f"{uuid4().hex}{suffix}"
    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return f"/static/generated/uploads/{destination.name}"
