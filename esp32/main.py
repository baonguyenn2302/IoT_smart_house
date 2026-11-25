from machine import I2C, Pin
import dht
import json
import network
import time
from umqtt.simple import MQTTClient
from secrets import (
    MQTT_BROKER,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_USER,
    WIFI_PASSWORD,
    WIFI_SSID,
)

# ===== CẤU HÌNH MQTT =====
MQTT_CLIENT_ID = "esp32_smarthouse"
TOPIC_SENSOR = b"sensors/data"
TOPIC_CONTROL = b"/devices/control"
TOPIC_RESPONSE = b"/devices/status"

# ===== CẤU HÌNH CẢM BIẾN =====
DHT_PIN_NUM = 13
dht_sensor = None

SDA_PIN = 19
SCL_PIN = 18
BH1750_ADDRS = (0x23, 0x5C)
BH1750_RETRY_MS = 5000
CONT_HIGH_RES_MODE = b"\x10"
i2c = None
bh1750_addr = None
bh1750_last_attempt = None

# ===== CẤU HÌNH LED =====
LED1_PIN = 25
LED2_PIN = 26
led1 = Pin(LED1_PIN, Pin.OUT)
led2 = Pin(LED2_PIN, Pin.OUT)
LEDS = {"led1": led1, "led2": led2}

client = None


def bh1750_init():
    global i2c, bh1750_addr, bh1750_last_attempt
    bh1750_addr = None
    bh1750_last_attempt = time.ticks_ms()

    try:
        if i2c is None:
            i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)
    except OSError as e:
        print("Khong khoi tao duoc I2C cua BH1750 (GY-302):", e)
        return

    last_error = "Khong co ACK"
    for addr in BH1750_ADDRS:
        try:
            if i2c.writeto(addr, CONT_HIGH_RES_MODE) != 1:
                continue
        except OSError as e:
            last_error = e
            continue

        bh1750_addr = addr
        print("Da ket noi BH1750 (GY-302) tai 0x{:02X}".format(addr))
        return

    print("Khong ket noi duoc BH1750 (GY-302) tai 0x23 hoac 0x5C:", last_error)


def bh1750_read_lux():
    global bh1750_addr, bh1750_last_attempt
    if bh1750_addr is None:
        if bh1750_last_attempt is None or time.ticks_diff(
            time.ticks_ms(), bh1750_last_attempt
        ) >= BH1750_RETRY_MS:
            bh1750_init()
        return None  # Nếu vừa kết nối lại, đọc vào chu kỳ sau để cảm biến đo xong.

    try:
        data = i2c.readfrom(bh1750_addr, 2)
    except OSError as e:
        print("Mat ket noi BH1750 (GY-302) khi doc anh sang:", e)
        bh1750_addr = None
        bh1750_last_attempt = time.ticks_ms()
        return None

    raw = (data[0] << 8) | data[1]
    return raw / 1.2


def doc_dht11():
    global dht_sensor
    try:
        if dht_sensor is None:
            dht_pin = Pin(DHT_PIN_NUM, Pin.IN, Pin.PULL_UP)
            dht_sensor = dht.DHT11(dht_pin)
        dht_sensor.measure()
        return dht_sensor.temperature(), dht_sensor.humidity()
    except Exception as e:  # Driver DHT dùng Exception cho lỗi checksum.
        print("Khong doc duoc cam bien DHT11 (GPIO {}):".format(DHT_PIN_NUM), e)
        return None, None


# ===== KẾT NỐI =====
def ket_noi_wifi(timeout=20):
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        print("Da ket noi WiFi. Dia chi IP ESP32:", wlan.ifconfig()[0])
        return

    # Reset trạng thái WiFi trước khi kết nối để tránh "Wifi Internal State Error"
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    wlan.disconnect()
    time.sleep(1)

    print("Dang ket noi WiFi...")
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    bat_dau = time.time()
    while not wlan.isconnected():
        if time.time() - bat_dau > timeout:
            raise OSError("Het thoi gian cho WiFi, trang thai: {}".format(wlan.status()))
        time.sleep(0.5)
    print("MQTT_BROKER:", MQTT_BROKER)
    print("MQTT_PORT:", MQTT_PORT)
    print("Da ket noi WiFi. Dia chi IP ESP32:", wlan.ifconfig()[0])


def ket_noi_mqtt():
    global client
    client = MQTTClient(
        MQTT_CLIENT_ID,
        MQTT_BROKER,
        port=MQTT_PORT,
        user=MQTT_USER,
        password=MQTT_PASSWORD,
    )
    client.set_callback(xu_ly_lenh)
    client.connect()
    client.subscribe(TOPIC_CONTROL)
    print("Da ket noi MQTT broker. Dang lang nghe topic:", TOPIC_CONTROL)
    # Bao backend trang thai thuc te ngay khi ket noi
    gui_trang_thai_led()


def khoi_phuc_ket_noi():
    while True:
        buoc = "WiFi"
        try:
            ket_noi_wifi()
            buoc = "MQTT broker"
            ket_noi_mqtt()
            print("Da khoi phuc ket noi")
            return
        except Exception as e:
            print("Khong ket noi duoc {}. Thu lai sau 3 giay:".format(buoc), e)
            time.sleep(3)


# ===== XỬ LÝ LỆNH ĐIỀU KHIỂN LED =====
def gui_trang_thai_led(thiet_bi="all", action_id=None):
    keys = LEDS if thiet_bi == "all" else (thiet_bi,)
    trang_thai = {key: "on" if LEDS[key].value() == 1 else "off" for key in keys}
    if action_id is not None:
        trang_thai["action_id"] = action_id
    payload = json.dumps(trang_thai)
    client.publish(TOPIC_RESPONSE, payload.encode())
    print("Da gui trang thai:", payload)


def xu_ly_lenh(topic, msg):
    lenh = msg.decode().strip().lower()
    print("Nhan lenh:", lenh)
    phan = lenh.split(":")
    try:
        if len(phan) not in (2, 3):
            raise ValueError()
        thiet_bi, trang_thai = phan[:2]
        if (thiet_bi != "all" and thiet_bi not in LEDS) or trang_thai not in ("on", "off"):
            raise ValueError()
        action_id = int(phan[2]) if len(phan) == 3 else None
        if action_id is not None and action_id <= 0:
            raise ValueError()
    except ValueError:
        print(">>> Lenh khong hop le:", lenh)
        return

    pins = LEDS.values() if thiet_bi == "all" else (LEDS[thiet_bi],)
    for pin in pins:
        pin.value(1 if trang_thai == "on" else 0)

    gui_trang_thai_led(thiet_bi if action_id is not None else "all", action_id)
    print(">>> Da thuc hien:", lenh)


# ===== ĐỌC VÀ GỬI CẢM BIẾN =====
def doc_va_gui_cam_bien():
    temp, hum = doc_dht11()
    lux = bh1750_read_lux()

    payload = '{{"temperature": {}, "humidity": {}, "lux": {}}}'.format(
        "{:.1f}".format(temp) if temp is not None else "null",
        "{:.1f}".format(hum) if hum is not None else "null",
        "{:.1f}".format(lux) if lux is not None else "null",
    )
    client.publish(TOPIC_SENSOR, payload)
    print("Da gui:", payload)


# ===== KHỞI ĐỘNG =====
def main():
    bh1750_init()
    time.sleep(2)  # cho DHT11 on dinh
    doc_dht11()  # Kiểm tra cảm biến trước khi chờ WiFi/MQTT.
    khoi_phuc_ket_noi()

    lan_thu = 1
    while True:
        try:
            client.check_msg()

            # Cu moi 5 vong (khoang 2.5 giay) gui du lieu cam bien 1 lan
            if lan_thu % 5 == 0:
                doc_va_gui_cam_bien()

            lan_thu += 1
        except OSError as e:
            print("Mat ket noi MQTT:", e)
            khoi_phuc_ket_noi()

        time.sleep(0.5)


if __name__ == "__main__":
    main()
