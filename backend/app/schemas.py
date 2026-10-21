from datetime import datetime
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import ActionStatus, ActionType, DeviceStatus

T = TypeVar("T")


class ORMModel(BaseModel):
    """Cho phép Pydantic đọc trực tiếp từ object SQLAlchemy."""
    model_config = ConfigDict(from_attributes=True)


# ===== Phân trang =====
class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


# ===== Device =====
class DeviceOut(ORMModel):
    id: int
    name: str
    status: DeviceStatus


class DeviceControlIn(BaseModel):
    action: ActionType = Field(description="Bật (ON) hoặc tắt (OFF)", examples=["ON"])


# ===== Sensor =====
class SensorOut(ORMModel):
    id: int
    name: str
    unit: Optional[str] = None
    min_normal: Optional[float] = None
    max_normal: Optional[float] = None


class SensorDataOut(ORMModel):
    id: int
    value: float
    recorded_at: datetime
    sensor_id: int
    sensor: SensorOut


class SensorLatestOut(BaseModel):
    sensor: SensorOut
    value: Optional[float] = None
    recorded_at: Optional[datetime] = None
    is_normal: Optional[bool] = None  # None khi chưa có dữ liệu


# ===== Action History =====
class ActorOut(ORMModel):
    id: int
    username: str
    full_name: Optional[str] = None


class ActionOut(ORMModel):
    id: int
    action: ActionType
    status: ActionStatus
    recorded_at: datetime
    device: DeviceOut
    user: Optional[ActorOut] = None  # None = hệ thống/tự động


# ===== Payload MQTT từ ESP32 =====
class SensorPayload(BaseModel):
    """Topic sensors/data: {"temperature": 28.5, "humidity": 65, "lux": 450}"""
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    lux: Optional[float] = None


class DeviceStatusPayload(BaseModel):
    """Topic /devices/status: {"led1": "on", "led2": "off"}"""
    led1: Optional[DeviceStatus] = None
    led2: Optional[DeviceStatus] = None

    @field_validator("led1", "led2", mode="before")
    @classmethod
    def normalize(cls, value):
        # ESP32 gửi chữ thường "on"/"off", enum cần "ON"/"OFF"
        if isinstance(value, str):
            return value.strip().upper()
        return value

# ===== Auth & User =====
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: int
    username: str
    full_name: Optional[str] = None
    student_id: Optional[str] = None
    class_name: Optional[str] = None
    faculty: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    links: Optional[dict] = None  # không trả về password