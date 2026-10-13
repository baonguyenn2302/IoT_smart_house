import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Double,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeviceStatus(str, enum.Enum):
    ON = "ON"
    OFF = "OFF"


class ActionType(str, enum.Enum):
    ON = "ON"
    OFF = "OFF"


class ActionStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # hash bcrypt
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    student_id: Mapped[Optional[str]] = mapped_column(String(20))
    class_name: Mapped[Optional[str]] = mapped_column(String(20))
    faculty: Mapped[Optional[str]] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    avatar: Mapped[Optional[str]] = mapped_column(String(255))
    links: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    actions: Mapped[list["ActionHistory"]] = relationship(back_populates="user")


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus), nullable=False, default=DeviceStatus.OFF
    )

    actions: Mapped[list["ActionHistory"]] = relationship(back_populates="device")


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    min_normal: Mapped[Optional[float]] = mapped_column(Double)
    max_normal: Mapped[Optional[float]] = mapped_column(Double)

    data: Mapped[list["DataSensor"]] = relationship(
        back_populates="sensor", cascade="all, delete-orphan", passive_deletes=True
    )


class DataSensor(Base):
    __tablename__ = "data_sensor"
    __table_args__ = (
        Index("idx_sensor_time", "sensor_id", "recorded_at"),
        Index("idx_time", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    value: Mapped[float] = mapped_column(Double, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False
    )

    sensor: Mapped["Sensor"] = relationship(back_populates="data")


class ActionHistory(Base):
    __tablename__ = "action_history"
    __table_args__ = (
        Index("idx_action_device_time", "device_id", "recorded_at"),
        Index("idx_action_status", "status"),
        Index("idx_action_time", "recorded_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action: Mapped[ActionType] = mapped_column(Enum(ActionType), nullable=False)
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus), nullable=False, default=ActionStatus.PENDING
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), nullable=False)

    user: Mapped[Optional["User"]] = relationship(back_populates="actions")
    device: Mapped["Device"] = relationship(back_populates="actions")