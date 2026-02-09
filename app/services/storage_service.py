"""Cloudflare R2 storage service for photo uploads."""

import logging
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile

from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _get_r2_client():
    """Create an S3 client configured for Cloudflare R2."""
    if not settings.R2_ACCOUNT_ID or not settings.R2_ACCESS_KEY_ID:
        return None
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def r2_is_configured() -> bool:
    """Check whether R2 credentials are configured."""
    return bool(
        settings.R2_ACCOUNT_ID
        and settings.R2_ACCESS_KEY_ID
        and settings.R2_BUCKET_NAME
    )


async def upload_photo(file: UploadFile) -> str:
    """Upload a photo to R2 and return the public URL."""
    if not r2_is_configured():
        raise HTTPException(status_code=500, detail="Photo storage is not configured")

    # Validate extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '.{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Read and validate size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

    # Generate unique key
    date_prefix = datetime.now().strftime("%Y/%m")
    unique_name = f"{uuid.uuid4().hex[:12]}.{ext}"
    key = f"batch-photos/{date_prefix}/{unique_name}"

    # Upload to R2
    client = _get_r2_client()
    if not client:
        raise HTTPException(status_code=500, detail="Could not connect to photo storage")

    content_type_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }

    try:
        client.put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=content,
            ContentType=content_type_map.get(ext, "application/octet-stream"),
        )
    except ClientError as e:
        logger.error(f"R2 upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload photo")

    public_url = settings.R2_PUBLIC_URL.rstrip("/")
    return f"{public_url}/{key}"
