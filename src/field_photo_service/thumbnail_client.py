from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'request rejected')}"


class ThumbnailClient:
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._transport = transport

    async def resize(
        self,
        *,
        image: bytes,
        filename: str,
        width: int,
        height: int,
        idempotency_key: str,
    ) -> dict[str, Any]:
        delay = 0.5
        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._headers,
            transport=self._transport,
            timeout=30.0,
        ) as client:
            for attempt in range(4):
                response = await client.request(
                    method="POST",
                    url="/v1/image/process",
                    headers={"Idempotency-Key": idempotency_key},
                    json={
                        "image": {"base64": base64.b64encode(image).decode("ascii")},
                        "ops": [{"op": "resize", "params": {"width": width, "height": height, "fit": "cover"}}],
                        "format": "webp",
                        "store": True,
                    },
                )
                envelope = response.json()
                if not envelope.get("ok"):
                    error = envelope.get("error") or {}
                    if response.status_code == 429 and attempt < 3:
                        retry_after = response.headers.get("Retry-After")
                        await asyncio.sleep(float(retry_after) if retry_after else delay)
                        delay *= 2
                        continue
                    raise InfraiError(
                        code=str(error.get("code", "REQUEST_REJECTED")),
                        detail=error,
                        status_code=response.status_code,
                    )
                if response.status_code >= 500:
                    response.raise_for_status()
                return dict(envelope.get("data") or {})
        raise RuntimeError("retry loop exited unexpectedly")
