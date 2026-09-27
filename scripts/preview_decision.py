from field_photo_service.follow_up_policy import (
    DispatchStatus,
    FollowUpInput,
    needs_technician_follow_up,
)


photo = FollowUpInput(
    work_order_id="WO-1842",
    dispatch_status=DispatchStatus.completed,
    technician_note=None,
)
print(
    {
        "work_order_id": photo.work_order_id,
        "follow_up_required": needs_technician_follow_up(photo),
    }
)
