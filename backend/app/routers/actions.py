import enum
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import ActionHistory, ActionStatus, ActionType, Device, User
from app.schemas import ActionOut, Page

router = APIRouter(prefix="/api/actions", tags=["Action History"])


class ActionSort(str, enum.Enum):
    TIME_DESC = "TIME_DESC"  # mới nhất trước
    TIME_ASC = "TIME_ASC"    # cũ nhất trước


@router.get(
    "",
    response_model=Page[ActionOut],
    summary="Lịch sử bật/tắt thiết bị",
    description="Dùng cho bảng Action History. Hỗ trợ tìm kiếm (q), lọc và sắp xếp theo thời gian.",
)
def list_actions(
    q: Optional[str] = Query(None, description="Từ khóa: tên thiết bị, người thao tác, ON/OFF, trạng thái, thời gian"),
    device_id: Optional[int] = Query(None, description="Lọc theo thiết bị (1=LED 1, 2=LED 2)"),
    status: Optional[ActionStatus] = Query(None, description="PENDING, SUCCESS hoặc FAILED"),
    action: Optional[ActionType] = Query(None, description="Lọc theo hành động: ON hoặc OFF"),
    from_time: Optional[datetime] = Query(None, alias="from"),
    to_time: Optional[datetime] = Query(None, alias="to"),
    sort: ActionSort = Query(ActionSort.TIME_DESC, description="Sắp xếp theo thời gian: TIME_DESC hoặc TIME_ASC"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = (
        select(ActionHistory)
        .join(Device, ActionHistory.device_id == Device.id)
        .outerjoin(User, ActionHistory.user_id == User.id)
        .options(joinedload(ActionHistory.device), joinedload(ActionHistory.user))
    )

    if q and q.strip():
        keyword = q.strip().replace("T", " ")
        pattern = f"%{keyword}%"
        time_vn = func.date_format(ActionHistory.recorded_at, "%d/%m/%Y %H:%i:%s")
        time_iso = func.date_format(ActionHistory.recorded_at, "%Y-%m-%d %H:%i:%s")
        query = query.where(
            or_(
                Device.name.like(pattern),
                User.full_name.like(pattern),
                User.username.like(pattern),
                cast(ActionHistory.action, String).like(pattern),
                cast(ActionHistory.status, String).like(pattern),
                time_vn.like(pattern),
                time_iso.like(pattern),
            )
        )

    if device_id is not None:
        query = query.where(ActionHistory.device_id == device_id)
    if status is not None:
        query = query.where(ActionHistory.status == status)
    if action is not None:
        query = query.where(ActionHistory.action == action)
    if from_time is not None:
        query = query.where(ActionHistory.recorded_at >= from_time)
    if to_time is not None:
        query = query.where(ActionHistory.recorded_at <= to_time)

    order_by = (
        (ActionHistory.recorded_at.desc(), ActionHistory.id.desc())
        if sort == ActionSort.TIME_DESC
        else (ActionHistory.recorded_at.asc(), ActionHistory.id.asc())
    )

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(*order_by)
        .offset((page - 1) * size)
        .limit(size)
    ).unique().all()

    return Page(items=items, total=total, page=page, size=size)