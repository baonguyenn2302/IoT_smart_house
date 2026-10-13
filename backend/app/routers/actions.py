from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import ActionHistory, ActionStatus, ActionType
from app.schemas import ActionOut, Page

router = APIRouter(prefix="/api/actions", tags=["Action History"])

import enum

class ActionSort(str, enum.Enum):
    TIME_DESC = "TIME_DESC"  # mới nhất trước
    TIME_ASC = "TIME_ASC"    # cũ nhất trước

@router.get(
    "",
    response_model=Page[ActionOut],
    summary="Lịch sử bật/tắt thiết bị",
    description="Dùng cho bảng Action History. Có thể lọc theo thiết bị, trạng thái và khoảng thời gian.",
)
def list_actions(
    device_id: Optional[int] = Query(None, description="Lọc theo thiết bị (1=LED 1, 2=LED 2)"),
    status: Optional[ActionStatus] = Query(None, description="PENDING, SUCCESS hoặc FAILED"),
    action: Optional[ActionType] = Query(None, description="Lọc theo hành động: ON hoặc OFF"),
    from_time: Optional[datetime] = Query(None, alias="from"),
    to_time: Optional[datetime] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    sort: ActionSort = Query(ActionSort.TIME_DESC, description="Sắp xếp theo thời gian: TIME_DESC hoặc TIME_ASC"),
    db: Session = Depends(get_db),
):
    query = select(ActionHistory).options(
        joinedload(ActionHistory.device),
        joinedload(ActionHistory.user),
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

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    order_by = (
        (ActionHistory.recorded_at.desc(), ActionHistory.id.desc())
        if sort == ActionSort.TIME_DESC
        else (ActionHistory.recorded_at.asc(), ActionHistory.id.asc())
    )

    items = db.scalars(
        query.order_by(*order_by)
        .offset((page - 1) * size)
        .limit(size)
    ).unique().all()

    return Page(items=items, total=total, page=page, size=size)