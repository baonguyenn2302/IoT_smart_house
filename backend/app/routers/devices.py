from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import as_vietnam_time
from app.database import get_db
from app.deps import get_current_user
from app.models import ActionHistory, ActionStatus, Device, DeviceStatus, User
from app.mqtt_service import ACK_TIMEOUT_SECONDS, MqttNotConnectedError, send_device_command
from app.schemas import ActionOut, DashboardDeviceOut, DeviceControlIn, DeviceOut

router = APIRouter(prefix="/api/devices", tags=["Devices"])


def _load_action(db: Session, action_id: int) -> ActionHistory:
    """Tải lại bản ghi kèm device và user để trả về an toàn, không phụ thuộc session."""
    return db.scalar(
        select(ActionHistory)
        .options(joinedload(ActionHistory.device), joinedload(ActionHistory.user))
        .where(ActionHistory.id == action_id)
        .execution_options(populate_existing=True)
    )


@router.get("", response_model=list[DeviceOut], summary="Danh sách thiết bị và trạng thái")
def list_devices(db: Session = Depends(get_db)):
    return db.scalars(select(Device).order_by(Device.id)).all()


@router.get(
    "/dashboard", response_model=list[DashboardDeviceOut], summary="Trạng thái công tắc trên Dashboard"
)
def list_dashboard_devices(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    cutoff = as_vietnam_time(now).replace(microsecond=0) - timedelta(seconds=ACK_TIMEOUT_SECONDS)
    pending = (
        select(ActionHistory.id)
        .where(
            ActionHistory.device_id == Device.id,
            ActionHistory.status == ActionStatus.PENDING,
            ActionHistory.recorded_at >= cutoff,
        )
        .exists()
    )
    rows = db.execute(select(Device, pending).order_by(Device.id)).all()
    utc_now = now.replace(tzinfo=None)

    devices = []
    for device, is_pending in rows:
        update_in_ms = device.display_update_in_ms(utc_now)
        status = device.status
        if update_in_ms:
            status = DeviceStatus.OFF if status == DeviceStatus.ON else DeviceStatus.ON
        devices.append(
            DashboardDeviceOut(
                id=device.id,
                name=device.name,
                status=status,
                pending=is_pending,
                update_in_ms=update_in_ms,
            )
        )
    return devices


@router.post(
    "/{device_id}/control",
    response_model=ActionOut,
    summary="Bật/tắt thiết bị",
    description="Tạo lệnh ở trạng thái PENDING và gửi qua MQTT. Trạng thái thực tế sẽ cập nhật khi ESP32 phản hồi.",
    responses={
        400: {"description": "Thiết bị chưa được cấu hình MQTT"},
        404: {"description": "Không tìm thấy thiết bị"},
        503: {"description": "Chưa kết nối được tới MQTT broker"},
    },
)
def control_device(
    device_id: int,
    body: DeviceControlIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy thiết bị")

    try:
        record = send_device_command(db, device, body.action, user_id=user.id)
    except MqttNotConnectedError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _load_action(db, record.id)
