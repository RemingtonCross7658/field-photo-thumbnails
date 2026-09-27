from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class DispatchStatus(str, Enum):
    assigned = "assigned"
    en_route = "en_route"
    on_site = "on_site"
    completed = "completed"


class PhotoContext(Protocol):
    dispatch_status: DispatchStatus
    technician_note: str | None


@dataclass(frozen=True)
class FollowUpInput:
    work_order_id: str
    dispatch_status: DispatchStatus
    technician_note: str | None = None


def needs_technician_follow_up(photo: PhotoContext) -> bool:
    if photo.dispatch_status is not DispatchStatus.completed:
        return False
    return not (photo.technician_note and photo.technician_note.strip())

