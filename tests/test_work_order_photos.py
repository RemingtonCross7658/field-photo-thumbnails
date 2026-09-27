from field_photo_service.follow_up_policy import (
    DispatchStatus,
    FollowUpInput,
    needs_technician_follow_up,
)


def test_completed_job_without_note_requires_follow_up() -> None:
    photo = FollowUpInput(
        work_order_id="WO-1842",
        dispatch_status=DispatchStatus.completed,
        technician_note="   ",
    )

    assert needs_technician_follow_up(photo) is True


def test_active_dispatch_does_not_request_follow_up() -> None:
    photo = FollowUpInput(
        work_order_id="WO-1843",
        dispatch_status=DispatchStatus.on_site,
        technician_note=None,
    )

    assert needs_technician_follow_up(photo) is False
