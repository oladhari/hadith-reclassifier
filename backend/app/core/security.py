"""Fail closed for local/experimental write and paid-processing endpoints."""
import hmac
from fastapi import Header, HTTPException
from app.core.config import settings


def require_admin_api_key(x_admin_api_key: str | None = Header(default=None)) -> None:
    expected = settings.ADMIN_API_KEY.get_secret_value()
    if not 32 <= len(expected) <= 256 or not expected.isascii():
        raise HTTPException(status_code=503, detail="Administrative API is disabled")
    if not x_admin_api_key or len(x_admin_api_key) > 256 or not hmac.compare_digest(
        x_admin_api_key.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")
