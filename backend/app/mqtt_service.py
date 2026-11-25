import json
import logging
import threading
from datetime import datetime, timezone
from typing import Optional

import paho.mqtt.client as mqtt
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings, vietnam_now
from app.database import SessionLocal
from app.models import (
    ActionHistory,
    ActionStatus,
    ActionType,
    DataSensor,
    Device,
    Sensor,
)
from app.schemas import DeviceStatusPayload, SensorPayload

logger = logging.getLogger("mqtt")

# Lưu ý: topic phải khớp đúng với code ESP32 (sensors/data không có "/" đầu)
TOPIC_SENSOR = "sensors/data"
TOPIC_STATUS = "/devices/status"
TOPIC_CONTROL = "/devices/control"

ACK_TIMEOUT_SECONDS = 5

# key trong payload cảm biến -> tên sensor trong bảng sensors (khớp seed.sql)
SENSOR_KEY_TO_NAME = {
    "temperature": "Temperature",
    "humidity": "Humidity",
    "lux": "Light",
}

# tên device trong bảng devices -> key trong payload và lệnh MQTT (khớp main.py của ESP32)
DEVICE_NAME_TO_KEY = {
    "LED 1": "led1",
    "LED 2": "led2",
}

_client: Optional[mqtt.Client] = None


class MqttNotConnectedError(Exception):
    """Ném ra khi backend chưa kết nối được tới MQTT broker."""


# ===== Kết nối =====
def _on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        logger.error("Kết nối MQTT thất bại: %s", reason_code)
        return
    logger.info("Đã kết nối MQTT broker")
    # Subscribe trong on_connect để tự đăng ký lại sau mỗi lần reconnect
    client.subscribe([(TOPIC_SENSOR, 0), (TOPIC_STATUS, 0)])


def _on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        if msg.topic == TOPIC_SENSOR:
            _handle_sensor_data(payload)
        elif msg.topic == TOPIC_STATUS:
            _handle_device_status(payload)
    except ValueError as e:
        # Bao gồm JSON sai định dạng và lỗi validate của Pydantic
        logger.warning("Payload không hợp lệ trên %s: %s", msg.topic, e)
    except Exception:
        logger.exception("Lỗi khi xử lý message trên %s", msg.topic)


# ===== Xử lý message đến =====
def _handle_sensor_data(raw: dict) -> None:
    data = SensorPayload.model_validate(raw)
    now = vietnam_now()

    with SessionLocal() as db:
        for key, value in data.model_dump().items():
            if value is None:
                continue
            sensor_name = SENSOR_KEY_TO_NAME[key]
            sensor_id = db.scalar(select(Sensor.id).where(Sensor.name == sensor_name))
            if sensor_id is None:
                logger.warning("Chưa có sensor '%s' trong database", sensor_name)
                continue
            db.add(DataSensor(sensor_id=sensor_id, value=value, recorded_at=now))
        db.commit()


def _handle_device_status(raw: dict) -> None:
    data = DeviceStatusPayload.model_validate(raw)
    acknowledged_at = datetime.now(timezone.utc).replace(tzinfo=None)

    with SessionLocal() as db:
        for device_name, key in DEVICE_NAME_TO_KEY.items():
            new_status = getattr(data, key)
            if new_status is None:
                continue

            device = db.scalar(
                select(Device).where(Device.name == device_name).with_for_update()
            )
            if device is None:
                continue

            if device.status != new_status:
                # Nếu đèn đảo chiều trong lúc chờ, nó trở về trạng thái Dashboard đang hiển thị.
                device.switch_at = (
                    None if device.display_update_in_ms(acknowledged_at) else acknowledged_at
                )
                device.status = new_status

            if data.action_id is not None:
                db.execute(
                    update(ActionHistory)
                    .where(
                        ActionHistory.id == data.action_id,
                        ActionHistory.device_id == device.id,
                        ActionHistory.action == ActionType(new_status.value),
                        ActionHistory.status == ActionStatus.PENDING,
                    )
                    .values(status=ActionStatus.SUCCESS)
                )

        db.commit()


# ===== Gửi lệnh điều khiển =====
def _mark_failed_if_pending(action_id: int) -> None:
    """Chạy sau ACK_TIMEOUT_SECONDS giây. Nếu lệnh vẫn PENDING thì coi là thất bại."""
    with SessionLocal() as db:
        result = db.execute(
            update(ActionHistory)
            .where(ActionHistory.id == action_id, ActionHistory.status == ActionStatus.PENDING)
            .values(status=ActionStatus.FAILED)
        )
        db.commit()
        if result.rowcount:
            logger.warning("Lệnh #%s không có phản hồi, đánh dấu FAILED", action_id)


def send_device_command(
    db: Session,
    device: Device,
    action: ActionType,
    user_id: Optional[int],
) -> ActionHistory:
    """Tạo bản ghi PENDING, publish lệnh lên MQTT và hẹn giờ kiểm tra timeout."""
    client = _client
    if client is None or not client.is_connected():
        raise MqttNotConnectedError("Chưa kết nối được tới MQTT broker")

    key = DEVICE_NAME_TO_KEY.get(device.name)
    if key is None:
        raise ValueError(f"Thiết bị '{device.name}' chưa được cấu hình MQTT")

    record = ActionHistory(
        action=action,
        status=ActionStatus.PENDING,
        device_id=device.id,
        user_id=user_id,
    )
    db.add(record)
    db.commit()  # commit trước khi publish để phản hồi từ ESP32 luôn tìm thấy bản ghi
    db.refresh(record)

    command = f"{key}:{action.value.lower()}:{record.id}"  # ví dụ "led1:on:42"
    result = client.publish(TOPIC_CONTROL, command, qos=0)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        record.status = ActionStatus.FAILED
        db.commit()
        raise MqttNotConnectedError("Không publish được lệnh lên MQTT")

    logger.info("Đã gửi lệnh '%s'", command)

    timer = threading.Timer(ACK_TIMEOUT_SECONDS, _mark_failed_if_pending, args=(record.id,))
    timer.daemon = True
    timer.start()

    return record


# ===== Vòng đời =====
def start_mqtt() -> None:
    global _client

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="fastapi_backend")
    client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
    client.on_connect = _on_connect
    client.on_message = _on_message

    # connect_async + loop_start: không chặn server nếu broker chưa bật, và tự thử lại
    client.connect_async(settings.MQTT_BROKER, settings.MQTT_PORT, keepalive=60)
    client.loop_start()
    _client = client


def stop_mqtt() -> None:
    global _client
    if _client is not None:
        _client.loop_stop()
        _client.disconnect()
        _client = None


def is_mqtt_connected() -> bool:
    return _client is not None and _client.is_connected()
