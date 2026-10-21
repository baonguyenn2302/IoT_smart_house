from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
import enum
from sqlalchemy import String, cast, func, or_

from app.database import get_db
from app.models import DataSensor, Sensor
from app.schemas import Page, SensorDataOut, SensorLatestOut, SensorOut

router = APIRouter(prefix="/api/sensors", tags=["Sensors"])

class SearchField(str, enum.Enum):
    ALL = "ALL"
    TIME = "TIME"
    TEMPERATURE = "TEMPERATURE"
    HUMIDITY = "HUMIDITY"
    LIGHT = "LIGHT"


SENSOR_NAME_BY_FIELD = {
    SearchField.TEMPERATURE: "Temperature",
    SearchField.HUMIDITY: "Humidity",
    SearchField.LIGHT: "Light",
}

class SortOrder(str, enum.Enum):
    TIME_DESC = "TIME_DESC"     # mới nhất trước
    TIME_ASC = "TIME_ASC"       # cũ nhất trước
    VALUE_DESC = "VALUE_DESC"   # giá trị giảm dần
    VALUE_ASC = "VALUE_ASC"     # giá trị tăng dần

def _is_normal(sensor: Sensor, value: Optional[float]) -> Optional[bool]:
    if value is None:
        return None
    if sensor.min_normal is not None and value < sensor.min_normal:
        return False
    if sensor.max_normal is not None and value > sensor.max_normal:
        return False
    return True


@router.get("", response_model=list[SensorOut], summary="Danh mục cảm biến và ngưỡng")
def list_sensors(db: Session = Depends(get_db)):
    return db.scalars(select(Sensor).order_by(Sensor.id)).all()


@router.get(
    "/latest",
    response_model=list[SensorLatestOut],
    summary="Giá trị mới nhất của từng cảm biến",
    description="Dùng cho 3 thẻ trên Dashboard. Trả về kèm `is_normal` theo ngưỡng trong bảng sensors.",
)
def latest_values(db: Session = Depends(get_db)):
    sensors = db.scalars(select(Sensor).order_by(Sensor.id)).all()
    result = []
    for sensor in sensors:
        latest = db.scalar(
            select(DataSensor)
            .where(DataSensor.sensor_id == sensor.id)
            .order_by(DataSensor.recorded_at.desc(), DataSensor.id.desc())
            .limit(1)
        )
        value = latest.value if latest else None
        result.append(
            SensorLatestOut(
                sensor=sensor,
                value=value,
                recorded_at=latest.recorded_at if latest else None,
                is_normal=_is_normal(sensor, value),
            )
        )
    return result


@router.get(
    "/data",
    response_model=Page[SensorDataOut],
    summary="Lịch sử đo, có lọc và phân trang",
    description="Dùng cho bảng Data Sensor và biểu đồ. Nếu không truyền `sensor_id`, trả về tất cả cảm biến.",
)
def list_sensor_data(
    q: Optional[str] = Query(None, description="Từ khóa tìm kiếm"),
    field: SearchField = Query(SearchField.ALL, description="Tìm theo: ALL, TIME, TEMPERATURE, HUMIDITY, LIGHT"),
    sensor_id: Optional[int] = Query(None, description="Lọc theo cảm biến (1=Temperature, 2=Humidity, 3=Light)"),
    from_time: Optional[datetime] = Query(None, alias="from", description="Thời gian bắt đầu, ví dụ 2026-08-19T12:00:00"),
    to_time: Optional[datetime] = Query(None, alias="to", description="Thời gian kết thúc"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=200),
    sort: SortOrder = Query(SortOrder.TIME_DESC, description="Sắp xếp: TIME_DESC, TIME_ASC, VALUE_DESC, VALUE_ASC"),
    db: Session = Depends(get_db),
):
    query = (
        select(DataSensor)
        .join(Sensor, DataSensor.sensor_id == Sensor.id)
        .options(joinedload(DataSensor.sensor))
    )

    if sensor_id is not None:
        query = query.where(DataSensor.sensor_id == sensor_id)
    if from_time is not None:
        query = query.where(DataSensor.recorded_at >= from_time)
    if to_time is not None:
        query = query.where(DataSensor.recorded_at <= to_time)

    if q and q.strip():
        # Cho phép gõ cả "T" thay cho khoảng trắng, ví dụ 2026-10-21T12:31:24
        keyword = q.strip().replace("T", " ")
        pattern = f"%{keyword}%"
        value_text = cast(DataSensor.value, String)
        # Hai định dạng thời gian: kiểu hiển thị (21/10/2026 12:31:24) và kiểu ISO (2026-10-21 12:31:24)
        time_vn = func.date_format(DataSensor.recorded_at, "%d/%m/%Y %H:%i:%s")
        time_iso = func.date_format(DataSensor.recorded_at, "%Y-%m-%d %H:%i:%s")
        time_match = or_(time_vn.like(pattern), time_iso.like(pattern))

        if field == SearchField.ALL:
            query = query.where(or_(Sensor.name.like(pattern), value_text.like(pattern), time_match))
        elif field == SearchField.TIME:
            query = query.where(time_match)
        else:
            query = query.where(
                Sensor.name == SENSOR_NAME_BY_FIELD[field],
                value_text.like(pattern),
            )

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    order_by = {
        SortOrder.TIME_DESC: (DataSensor.recorded_at.desc(), DataSensor.id.desc()),
        SortOrder.TIME_ASC: (DataSensor.recorded_at.asc(), DataSensor.id.asc()),
        SortOrder.VALUE_DESC: (DataSensor.value.desc(), DataSensor.id.desc()),
        SortOrder.VALUE_ASC: (DataSensor.value.asc(), DataSensor.id.asc()),
    }[sort]

    items = db.scalars(
        query.order_by(*order_by)
        .offset((page - 1) * size)
        .limit(size)
    ).unique().all()

    return Page(items=items, total=total, page=page, size=size)