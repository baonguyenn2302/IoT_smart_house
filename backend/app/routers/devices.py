from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.deps import get_current_user
from app.models import ActionHistory, Device, User
from app.mqtt_service import MqttNotConnectedError, send_device_command
from app.schemas import ActionOut, DeviceControlIn, DeviceOut

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