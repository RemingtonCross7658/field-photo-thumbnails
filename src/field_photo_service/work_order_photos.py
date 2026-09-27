from __future__ import annotations

import hashlib
import os
from typing import Annotated, Any

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .follow_up_policy import DispatchStatus, needs_technician_follow_up
from .thumbnail_client import InfraiError, ThumbnailClient


class WorkOrderPhoto(BaseModel):
    work_order_id: str = Field(min_length=1, max_length=80)
    dispatch_status: DispatchStatus
    technician_note: str | None = Field(default=None, max_length=500)


class ThumbnailResult(BaseModel):
    width: int
    height: int
    image: dict[str, Any]


class PhotoIntakeResult(BaseModel):
    work_order_id: str
    dispatch_status: DispatchStatus
    follow_up_required: bool
    thumbnails: list[ThumbnailResult]


def create_service(client: ThumbnailClient | None = None) -> FastAPI:
    app = FastAPI(title="Field photo thumbnails")

    @app.post("/work-orders/photos", response_model=PhotoIntakeResult)
    async def accept_photo(
        work_order_id: Annotated[str, Form(min_length=1, max_length=80)],
        dispatch_status: Annotated[DispatchStatus, Form()],
        photo: Annotated[UploadFile, File()],
        technician_note: Annotated[str | None, Form(max_length=500)] = None,
    ) -> PhotoIntakeResult:
        intake = WorkOrderPhoto(
            work_order_id=work_order_id,
            dispatch_status=dispatch_status,
            technician_note=technician_note,
        )
        image = await photo.read()
        if not image:
            raise HTTPException(status_code=400, detail="Photo is empty")

        active_client = client
        if active_client is None:
            api_key = os.environ.get("INFRAI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=503, detail="INFRAI_API_KEY is not configured")
            active_client = ThumbnailClient(api_key)

        digest = hashlib.sha256(image).hexdigest()[:16]
        sizes = ((320, 240), (960, 720))
        thumbnails: list[ThumbnailResult] = []
        try:
            for width, height in sizes:
                result = await active_client.resize(
                    image=image,
                    filename=photo.filename or "work-order-photo",
                    width=width,
                    height=height,
                    idempotency_key=f"{work_order_id}:{digest}:{width}x{height}",
                )
                thumbnails.append(ThumbnailResult(width=width, height=height, image=result))
        except InfraiError as exc:
            status = exc.status_code if 400 <= exc.status_code < 500 else 502
            raise HTTPException(status_code=status, detail={"code": exc.code, **exc.detail}) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="Image processing transport error") from exc

        return PhotoIntakeResult(
            work_order_id=work_order_id,
            dispatch_status=dispatch_status,
            follow_up_required=needs_technician_follow_up(intake),
            thumbnails=thumbnails,
        )

    return app


service = create_service()
