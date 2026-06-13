from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any


def sha256_json(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64url(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def sign_token(payload: dict[str, Any], secret: str) -> str:
    body = _b64url(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256)
    return f"{body}.{_b64url(signature.digest())}"


def verify_token(token: str, secret: str) -> dict[str, Any] | None:
    try:
        body, signature = token.split(".", 1)
    except ValueError:
        return None
    expected = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256)
    if not hmac.compare_digest(_b64url(expected.digest()), signature):
        return None
    try:
        return json.loads(_unb64url(body))
    except (json.JSONDecodeError, ValueError):
        return None
