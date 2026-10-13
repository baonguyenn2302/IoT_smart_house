from machine import I2C, Pin
import dht
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
dht_pin = Pin(DHT_PIN_NUM, Pin.IN, Pin.PULL_UP)
dht_sensor = dht.DHT11(dht_pin)

SDA_PIN = 19
SCL_PIN = 18
BH1750_ADDR = 0x23
POWER_ON = 0x01
RESET = 0x07
CONT_HIGH_RES_MODE = 0x10
i2c = I2C(0, scl=Pin(SCL_PIN), sda=Pin(SDA_PIN), freq=400000)

# ===== CẤU HÌNH LED =====
LED1_PIN = 25
LED2_PIN = 26
led1 = Pin(LED1_PIN, Pin.OUT)
led2 = Pin(LED2_PIN, Pin.OUT)

client = None


def bh1750_init():
    i2c.writeto(BH1750_ADDR, bytes([POWER_ON]))
    i2c.writeto(BH1750_ADDR, bytes([RESET]))
    i2c.writeto(BH1750_ADDR, bytes([CONT_HIGH_RES_MODE]))


def bh1750_read_lux():
    data = i2c.readfrom(BH1750_ADDR, 2)
    raw = (data[0] << 8) | data[1]
    return raw / 1.2


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
        try:
            ket_noi_wifi()
            ket_noi_mqtt()
            print("Da khoi phuc ket noi")
            return
        except OSError as e:
            print("Ket noi that bai, thu lai sau 3 giay:", e)
            time.sleep(3)


# ===== XỬ LÝ LỆNH ĐIỀU KHIỂN LED =====
def gui_trang_thai_led():
    trang_thai = '{{"led1": "{}", "led2": "{}"}}'.format(
        "on" if led1.value() == 1 else "off",
        "on" if led2.value() == 1 else "off",
    )
    client.publish(TOPIC_RESPONSE, trang_thai)
    print("Da gui trang thai:", trang_thai)


def xu_ly_lenh(topic, msg):
    lenh = msg.decode().strip().lower()
    print("Nhan lenh:", lenh)
    if lenh == "led1:on":
        led1.value(1)
    elif lenh == "led1:off":
        led1.value(0)
    elif lenh == "led2:on":
        led2.value(1)
    elif lenh == "led2:off":
        led2.value(0)
    elif lenh == "all:on":
        led1.value(1)
        led2.value(1)
    elif lenh == "all:off":
        led1.value(0)
        led2.value(0)
    else:
        print(">>> Lenh khong hop le:", lenh)
        return

    print(">>> Da thuc hien:", lenh)
    gui_trang_thai_led()


# ===== ĐỌC VÀ GỬI CẢM BIẾN =====
def doc_va_gui_cam_bien():
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
    except OSError as e:
        temp, hum = None, None
        print("Loi doc DHT11:", e)

    try:
        lux = bh1750_read_lux()
    except OSError as e:
        lux = None
        print("Loi doc GY-302:", e)

    payload = '{{"temperature": {}, "humidity": {}, "lux": {}}}'.format(
        "{:.1f}".format(temp) if temp is not None else "null",
        "{:.1f}".format(hum) if hum is not None else "null",
        "{:.1f}".format(lux) if lux is not None else "null",
    )
    client.publish(TOPIC_SENSOR, payload)
    print("Da gui:", payload)


# ===== KHỞI ĐỘNG =====
bh1750_init()
khoi_phuc_ket_noi()
time.sleep(2)  # cho DHT11 on dinh

lan_thu = 1
while True:
    try:
        client.check_msg()

        # Cu moi 5 vong (khoang 2.5 giay) gui du lieu cam bien 1 lan
        if lan_thu % 5 == 0:
            doc_va_gui_cam_bien()

        lan_thu += 1
    except OSError as e:
        print("Mat ket noi:", e)
        khoi_phuc_ket_noi()

    time.sleep(0.5)
