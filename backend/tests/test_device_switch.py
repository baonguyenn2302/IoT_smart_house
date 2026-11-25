import os
import unittest
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

for key in ("DB_USER", "DB_PASSWORD", "MQTT_USER", "MQTT_PASSWORD", "JWT_SECRET"):
    os.environ.setdefault(key, "test")

from app import config, mqtt_service
from app.database import Base
from app.models import ActionHistory, ActionStatus, ActionType, Device, DeviceStatus
from app.routers import devices


class DeviceSwitchTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        self.sessions = sessionmaker(bind=engine)
        with self.sessions.begin() as db:
            db.add_all([Device(id=1, name="LED 1"), Device(id=2, name="LED 2")])

        self.clock = datetime.now(timezone.utc)
        patches = ExitStack()
        self.addCleanup(patches.close)
        patches.enter_context(patch.object(mqtt_service, "SessionLocal", self.sessions))
        for module in (config, mqtt_service, devices):
            module_clock = patches.enter_context(patch.object(module, "datetime"))
            module_clock.now.side_effect = lambda tz: self.clock.astimezone(tz)

    def create_action(self, action, **fields):
        with self.sessions.begin() as db:
            record = ActionHistory(device_id=1, action=action, **fields)
            db.add(record)
            db.flush()
            return record.id

    def dashboard(self, device_id=1):
        with self.sessions() as db:
            return devices.list_dashboard_devices(db)[device_id - 1]

    def action_status(self, action_id):
        with self.sessions() as db:
            return db.get(ActionHistory, action_id).status

    def test_each_transition_waits_one_second_after_ack(self):
        for previous, target in [(DeviceStatus.OFF, DeviceStatus.ON), (DeviceStatus.ON, DeviceStatus.OFF)]:
            with self.subTest(target=target):
                action_id = self.create_action(ActionType(target.value))
                self.clock += timedelta(seconds=4, milliseconds=800)
                self.assertEqual(self.dashboard().status, previous)
                self.assertTrue(self.dashboard().pending)

                mqtt_service._handle_device_status({"led1": target.value, "action_id": action_id})
                with self.sessions() as db:
                    self.assertEqual(devices.list_devices(db)[0].status, target)
                self.assertEqual(self.dashboard().update_in_ms, 1000)
                mqtt_service._mark_failed_if_pending(action_id)
                self.assertEqual(self.action_status(action_id), ActionStatus.SUCCESS)

                self.clock += timedelta(milliseconds=999)
                self.assertEqual(self.dashboard().status, previous)
                self.assertEqual(self.dashboard().update_in_ms, 1)
                self.clock += timedelta(milliseconds=1)
                self.assertEqual(self.dashboard().status, target)
                self.assertEqual(self.dashboard().update_in_ms, 0)

    def test_unrelated_reports_do_not_confirm_a_command(self):
        action_id = self.create_action(ActionType.ON)
        for report in (
            {"led2": "on", "action_id": action_id},
            {"led1": "off", "action_id": action_id},
            {"led1": "on", "action_id": action_id + 1},
            {"led1": "on"},
        ):
            mqtt_service._handle_device_status(report)
            self.assertEqual(self.action_status(action_id), ActionStatus.PENDING)

        with self.assertLogs("mqtt", level="WARNING"):
            mqtt_service._mark_failed_if_pending(action_id)
        self.assertEqual(self.action_status(action_id), ActionStatus.FAILED)
        self.assertFalse(self.dashboard().pending)

    def test_quick_reversal_keeps_the_displayed_state(self):
        mqtt_service._handle_device_status({"led1": "on"})
        self.clock += timedelta(milliseconds=500)
        mqtt_service._handle_device_status({"led1": "on"})
        self.assertEqual(self.dashboard().update_in_ms, 500)

        mqtt_service._handle_device_status({"led1": "off", "led2": "on"})
        self.assertEqual(self.dashboard().status, DeviceStatus.OFF)
        self.assertEqual(self.dashboard().update_in_ms, 0)
        self.assertEqual(self.dashboard(2).status, DeviceStatus.OFF)
        self.assertEqual(self.dashboard(2).update_in_ms, 1000)

    def test_expired_pending_from_previous_run_does_not_block_switch(self):
        self.create_action(ActionType.ON, recorded_at=datetime(2000, 1, 1))
        self.assertFalse(self.dashboard().pending)
        self.assertEqual(self.dashboard().status, DeviceStatus.OFF)

    def test_control_publishes_the_action_id(self):
        client = Mock()
        client.is_connected.return_value = True
        client.publish.return_value.rc = mqtt_service.mqtt.MQTT_ERR_SUCCESS

        with patch.object(mqtt_service, "_client", client), patch.object(mqtt_service.threading, "Timer"):
            with self.sessions() as db:
                record = mqtt_service.send_device_command(db, db.get(Device, 1), ActionType.ON, user_id=None)

        client.publish.assert_called_once_with(mqtt_service.TOPIC_CONTROL, f"led1:on:{record.id}", qos=0)
        self.assertEqual(self.action_status(record.id), ActionStatus.PENDING)
