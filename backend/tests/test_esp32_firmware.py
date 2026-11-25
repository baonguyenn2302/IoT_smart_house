import importlib.util
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, patch


class Pin:
    IN, OUT, PULL_UP = range(3)

    def __init__(self, *_):
        self.level = 0

    def value(self, level=None):
        if level is not None:
            self.level = level
        return self.level


class Esp32FirmwareTest(unittest.TestCase):
    def setUp(self):
        self.i2c = Mock()
        self.i2c.writeto.return_value = 1
        self.i2c.readfrom.return_value = b"\x00\x78"
        self.mqtt = Mock()
        self.dht = Mock(temperature=Mock(return_value=26), humidity=Mock(return_value=60))
        wlan = Mock(isconnected=Mock(return_value=True), ifconfig=Mock(return_value=("127.0.0.1",)))
        modules = {
            "machine": SimpleNamespace(Pin=Pin, I2C=Mock(return_value=self.i2c)),
            "dht": SimpleNamespace(DHT11=Mock(return_value=self.dht)),
            "network": SimpleNamespace(STA_IF=0, WLAN=Mock(return_value=wlan)),
            "umqtt.simple": SimpleNamespace(MQTTClient=Mock(return_value=self.mqtt)),
            "secrets": SimpleNamespace(
                MQTT_BROKER="localhost", MQTT_PORT=1883, MQTT_USER="", MQTT_PASSWORD="",
                WIFI_SSID="", WIFI_PASSWORD="",
            ),
        }
        path = Path(__file__).resolve().parents[2] / "esp32" / "main.py"
        spec = importlib.util.spec_from_file_location("esp32_firmware", path)
        self.firmware = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(self.firmware)

        self.firmware.time = SimpleNamespace(
            sleep=Mock(), ticks_ms=Mock(return_value=0), ticks_diff=lambda now, then: now - then,
        )
        output = patch("builtins.print")
        self.log = output.start()
        self.addCleanup(output.stop)

    def test_missing_bh1750_keeps_led_and_dht_running(self):
        self.i2c.writeto.side_effect = OSError(19, "ENODEV")
        self.firmware.time.sleep.side_effect = [None] * 5 + [KeyboardInterrupt]

        def check_message():
            if self.mqtt.check_msg.call_count == 1:
                callback = self.mqtt.set_callback.call_args.args[0]
                callback(b"/devices/control", b"led1:on:123")

        self.mqtt.check_msg.side_effect = check_message
        with self.assertRaises(KeyboardInterrupt):
            self.firmware.main()

        self.mqtt.connect.assert_called_once()
        self.i2c.readfrom.assert_not_called()
        self.assertEqual(self.firmware.led1.value(), 1)
        self.assertTrue(any("BH1750 (GY-302)" in logged.args[0] for logged in self.log.call_args_list))
        payloads = [(sent.args[0], json.loads(sent.args[1])) for sent in self.mqtt.publish.call_args_list]
        self.assertIn((b"/devices/status", {"led1": "on", "action_id": 123}), payloads)
        self.assertIn((b"sensors/data", {"temperature": 26, "humidity": 60, "lux": None}), payloads)

    def test_dht11_error_is_logged_and_lux_is_still_published(self):
        self.dht.measure.side_effect = Exception("checksum error")
        self.firmware.client = self.mqtt
        self.firmware.bh1750_init()
        self.firmware.doc_va_gui_cam_bien()

        self.assertTrue(any("DHT11" in logged.args[0] for logged in self.log.call_args_list))
        topic, payload = self.mqtt.publish.call_args.args
        self.assertEqual(topic, b"sensors/data")
        self.assertEqual(json.loads(payload), {"temperature": None, "humidity": None, "lux": 100})

    def test_uses_second_address_when_first_does_not_acknowledge(self):
        self.i2c.writeto.side_effect = [0, 1]
        self.firmware.bh1750_init()

        self.assertEqual(self.i2c.writeto.call_args_list, [call(0x23, b"\x10"), call(0x5C, b"\x10")])
        self.assertEqual(self.firmware.bh1750_read_lux(), 100)
        self.i2c.readfrom.assert_called_once_with(0x5C, 2)

    def test_read_error_retries_and_recovers_lux(self):
        self.i2c.readfrom.side_effect = [OSError(19, "ENODEV"), b"\x00\x78"]
        self.firmware.bh1750_init()
        self.assertIsNone(self.firmware.bh1750_read_lux())

        self.firmware.time.ticks_ms.return_value = self.firmware.BH1750_RETRY_MS - 1
        self.assertIsNone(self.firmware.bh1750_read_lux())
        self.assertEqual(self.i2c.writeto.call_count, 1)

        self.firmware.time.ticks_ms.return_value += 1
        self.assertIsNone(self.firmware.bh1750_read_lux())
        self.assertEqual(self.i2c.writeto.call_count, 2)
        self.assertEqual(self.firmware.bh1750_read_lux(), 100)

    def test_led_status_is_published_after_gpio_write(self):
        self.firmware.client = self.mqtt

        def check_status(topic, payload):
            self.assertEqual(topic, b"/devices/status")
            self.assertEqual(self.firmware.led2.value(), 1)
            self.assertEqual(json.loads(payload), {"led2": "on", "action_id": 42})

        self.mqtt.publish.side_effect = check_status
        self.firmware.xu_ly_lenh(b"/devices/control", b"led2:on:42")
        self.mqtt.publish.assert_called_once()
