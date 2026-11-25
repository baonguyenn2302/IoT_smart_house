import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

for key in ("DB_USER", "DB_PASSWORD", "MQTT_USER", "MQTT_PASSWORD", "JWT_SECRET"):
    os.environ.setdefault(key, "test")

from app import config, mqtt_service
from app.database import Base
from app.models import ActionHistory, ActionType, DataSensor, Device, Sensor
from app.routers.actions import ActionSort, list_actions
from app.schemas import ActionOut


class HistoryTimeTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        self.sessions = sessionmaker(bind=engine)
        with self.sessions.begin() as db:
            db.add_all([Device(id=1, name="LED 1"), Sensor(name="Temperature")])
            db.add_all([
                ActionHistory(
                    device_id=1, action=ActionType.ON, recorded_at=datetime(2026, 11, 25, 23, 59, 59),
                ),
                ActionHistory(
                    device_id=1, action=ActionType.OFF, recorded_at=datetime(2026, 11, 26, 0, 0, 7),
                ),
            ])

    def test_saved_action_is_returned_as_recorded(self):
        with self.sessions() as db:
            record = db.get(ActionHistory, 2)
            output = ActionOut.model_validate(record).model_dump(mode="json")

        self.assertEqual(output["recorded_at"], "2026-11-26T00:00:07")

    def test_action_date_range_accepts_vietnam_time_or_explicit_offset(self):
        for start, end in (
            ("2026-11-26T00:00:00", "2026-11-26T00:00:07"),
            ("2026-11-25T17:00:00+00:00", "2026-11-25T17:00:07+00:00"),
        ):
            with self.subTest(start=start), self.sessions() as db:
                result = list_actions(
                    q=None,
                    device_id=None,
                    status=None,
                    action=None,
                    from_time=datetime.fromisoformat(start),
                    to_time=datetime.fromisoformat(end),
                    sort=ActionSort.TIME_DESC,
                    page=1,
                    size=10,
                    db=db,
                )
                self.assertEqual(result.total, 1)
                output = result.model_dump(mode="json")
                self.assertEqual(output["items"][0]["recorded_at"], "2026-11-26T00:00:07")

    def test_sensor_samples_and_new_actions_are_saved_in_vietnam_time(self):
        now = datetime(2026, 11, 25, 17, 0, 7, tzinfo=timezone.utc)
        with (
            patch.object(mqtt_service, "SessionLocal", self.sessions),
            patch.object(config, "datetime") as clock,
        ):
            clock.now.side_effect = now.astimezone
            mqtt_service._handle_sensor_data({"temperature": 27})
            with self.sessions.begin() as db:
                action = ActionHistory(device_id=1, action=ActionType.ON)
                db.add(action)
                db.flush()
                action_id = action.id

        with self.sessions() as db:
            expected = datetime(2026, 11, 26, 0, 0, 7)
            self.assertEqual(db.scalar(select(DataSensor.recorded_at)), expected)
            self.assertEqual(db.get(ActionHistory, action_id).recorded_at, expected)
