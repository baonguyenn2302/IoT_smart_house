import math
import random
from datetime import datetime, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import (
    ActionHistory,
    ActionStatus,
    ActionType,
    DataSensor,
    Device,
    DeviceStatus,
    Sensor,
    User,
)


def seed_mock_data():
    db = SessionLocal()
    try:
        print("Đang kiểm tra và khởi tạo dữ liệu mẫu...")

        # 1. Khởi tạo User mẫu nếu chưa có
        user = db.scalar(select(User).where(User.username == "baonguyenn2302"))
        if not user:
            user = User(
                username="baonguyenn2302",
                password="hashed_password_mock",
                full_name="Nguyễn Gia Bảo",
                student_id="B21DCCN000",
                class_name="D21CQCN01-B",
                faculty="Công nghệ thông tin",
                email="baonguyen@example.com",
                phone="0987654321",
                avatar="",
                links={"github": "https://github.com", "report_pdf": ""},
            )
            db.add(user)
            db.flush()

        # 2. Khởi tạo Devices nếu chưa có
        devices = {d.id: d for d in db.scalars(select(Device)).all()}
        if 1 not in devices:
            d1 = Device(id=1, name="LED 1", status=DeviceStatus.OFF)
            db.add(d1)
        if 2 not in devices:
            d2 = Device(id=2, name="LED 2", status=DeviceStatus.OFF)
            db.add(d2)
        db.flush()

        # 3. Khởi tạo Sensors nếu chưa có
        sensors = {s.id: s for s in db.scalars(select(Sensor)).all()}
        if 1 not in sensors:
            db.add(Sensor(id=1, name="Temperature", unit="°C", min_normal=18.0, max_normal=35.0))
        if 2 not in sensors:
            db.add(Sensor(id=2, name="Humidity", unit="%", min_normal=40.0, max_normal=80.0))
        if 3 not in sensors:
            db.add(Sensor(id=3, name="Light", unit="lux", min_normal=100.0, max_normal=800.0))
        db.flush()

        # 4. Sinh 60 lần đo cảm biến trong 60 phút qua (mỗi phút 1 bản ghi cho 3 cảm biến)
        now = datetime.now()
        sensor_records = []
        for i in range(60, 0, -1):
            t = now - timedelta(minutes=i)
            # Tạo dao động thực tế theo hàm sin + nhiễu ngẫu nhiên
            temp_val = round(28.0 + math.sin(i / 5.0) * 2.5 + random.uniform(-0.3, 0.3), 1)
            hum_val = round(65.0 + math.sin(i / 7.0) * 8.0 + random.uniform(-1.0, 1.0), 1)
            lux_val = round(450.0 + math.sin(i / 4.0) * 120.0 + random.uniform(-15.0, 15.0), 1)

            sensor_records.append(DataSensor(sensor_id=1, value=temp_val, recorded_at=t))
            sensor_records.append(DataSensor(sensor_id=2, value=hum_val, recorded_at=t))
            sensor_records.append(DataSensor(sensor_id=3, value=lux_val, recorded_at=t))

        db.add_all(sensor_records)

        # 5. Sinh lịch sử thao tác bật/tắt (Action History)
        actions = []
        for i in range(20, 0, -1):
            t = now - timedelta(minutes=i * 4)
            dev_id = 1 if i % 2 == 1 else 2
            act = ActionType.ON if i % 3 != 0 else ActionType.OFF
            stat = ActionStatus.SUCCESS if i % 5 != 0 else ActionStatus.FAILED
            actions.append(
                ActionHistory(
                    action=act,
                    status=stat,
                    recorded_at=t,
                    user_id=user.id if i % 3 != 0 else None,
                    device_id=dev_id,
                )
            )

        db.add_all(actions)
        db.commit()
        print(f"✅ Đã tạo thành công {len(sensor_records)} bản ghi đo cảm biến và {len(actions)} bản ghi lịch sử điều khiển!")

    except Exception as e:
        db.rollback()
        print(f"❌ Lỗi khi tạo dữ liệu mẫu: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_mock_data()
