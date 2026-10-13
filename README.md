# 🏠 Smart House IoT System

Hệ thống giám sát môi trường và điều khiển thiết bị thông minh theo thời gian thực (Real-time IoT Smart House). Dự án bao gồm mạch vi điều khiển ESP32 giao tiếp qua MQTT Broker, Backend xây dựng bằng FastAPI kết hợp cơ sở dữ liệu MySQL, và giao diện Web Dashboard trực quan bằng React + Vite.

---

## 📌 Mục lục
- [1. Tính năng nổi bật](#1-tính-năng-nổi-bật)
- [2. Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
- [3. Sơ đồ phần cứng & Kết nối ESP32](#3-sơ-đồ-phần-cứng--kết-nối-esp32)
- [4. MQTT Topics & Định dạng dữ liệu](#4-mqtt-topics--định-dạng-dữ-liệu)
- [5. Cấu trúc thư mục](#5-cấu-trúc-thư-mục)
- [6. Yêu cầu môi trường](#6-yêu-cầu-môi-trường)
- [7. Hướng dẫn cài đặt & Khởi chạy](#7-hướng-dẫn-cài-đặt--khởi-chạy)
- [8. Danh sách RESTful API](#8-danh-sách-restful-api)
- [9. Bảo mật & Quản lý môi trường](#9-bảo-mật--quản-lý-môi-trường)

---

## 1. Tính năng nổi bật

- 🌡️ **Giám sát môi trường thời gian thực:** Thu thập các thông số nhiệt độ (°C), độ ẩm (%) và cường độ ánh sáng (lux) từ cảm biến DHT11 và BH1750 (GY-302).
- 💡 **Điều khiển thiết bị hai chiều (Two-way Control):** Bật/tắt các đèn LED (LED 1, LED 2) từ giao diện Web, xác nhận trạng thái thực tế từ ESP32 qua cơ chế `PENDING` ➔ `SUCCESS` / `FAILED`.
- 📊 **Trực quan hóa dữ liệu & Biểu đồ:** Thống kê lịch sử đo, hiển thị biểu đồ biến thiên liên tục với Recharts. Cảnh báo vượt ngưỡng bình thường (`min_normal`, `max_normal`).
- 🔍 **Tìm kiếm & Phân trang đa năng:** Lọc lịch sử đo cảm biến và lịch sử thao tác theo thời gian, theo thiết bị, theo trạng thái, từ khóa đa trường.
- 🔄 **Chế độ Mock Data linh hoạt:** Frontend hỗ trợ mock adapter để kiểm thử giao diện độc lập; Backend hỗ trợ script seed dữ liệu mẫu vào MySQL.

---

## 2. Kiến trúc hệ thống

```
+--------------------+               +--------------------+
|    ESP32 Module    | <=== MQTT ==> |    MQTT Broker     |
| (DHT11, BH1750,    |    (1883)     |    (Mosquitto)     |
|  2x LEDs Control)  |               +---------^----------+
+--------------------+                         |
                                            MQTT Client
                                               |
+--------------------+               +---------v----------+
|  Frontend Web App  | <=== REST === |    FastAPI App     |
| (React 19 + Vite)  |    (8000)     |  (SQLAlchemy 2.0)  |
+--------------------+               +---------^----------+
                                               |
                                            PyMySQL
                                               |
                                     +---------v----------+
                                     |    MySQL Database  |
                                     |   (`smart_house`)  |
                                     +--------------------+
```

---

## 3. Sơ đồ phần cứng & Kết nối ESP32

Vi điều khiển ESP32 chạy firmware **MicroPython**:

| Thành phần | Loại | Chân ESP32 | Ghi chú |
| :--- | :--- | :--- | :--- |
| **DHT11** | Cảm biến Nhiệt độ & Độ ẩm | **GPIO 13** | Pin DATA (kèm trở kéo lên / Internal Pull-up) |
| **BH1750 (GY-302)** | Cảm biến Ánh sáng (I2C) | **SDA: GPIO 19**<br>**SCL: GPIO 18** | Địa chỉ I2C: `0x23`, Tần số I2C: 400kHz |
| **LED 1** | Thiết bị đầu ra | **GPIO 25** | Điều khiển ON (HIGH) / OFF (LOW) |
| **LED 2** | Thiết bị đầu ra | **GPIO 26** | Điều khiển ON (HIGH) / OFF (LOW) |

---

## 4. MQTT Topics & Định dạng dữ liệu

| Topic | Chiều | Định dạng Payload | Ví dụ |
| :--- | :--- | :--- | :--- |
| `sensors/data` | ESP32 ➔ Broker ➔ Backend | JSON | `{"temperature": 28.5, "humidity": 65.0, "lux": 450.0}` |
| `/devices/control` | Backend ➔ Broker ➔ ESP32 | Text string | `led1:on`, `led1:off`, `led2:on`, `led2:off`, `all:on`, `all:off` |
| `/devices/status` | ESP32 ➔ Broker ➔ Backend | JSON | `{"led1": "on", "led2": "off"}` |

---

## 5. Cấu trúc thư mục

```text
smart_house/
├── .gitignore                   # Cấu hình bỏ qua tệp ở cấp độ root
├── README.md                    # Tài liệu hướng dẫn dự án
├── run.txt                      # Bảng lệnh tổng hợp khởi chạy nhanh
│
├── database/                    # Script khởi tạo và định nghĩa CSDL
│   ├── init.sql                 # Tạo Database & User MySQL
│   ├── schema.sql               # Tạo cấu trúc các bảng (DDL)
│   └── seed.sql                 # Dữ liệu khởi tạo mặc định (Devices, Sensors)
│
├── backend/                     # Mã nguồn Backend FastAPI
│   ├── .env.example             # Mẫu cấu hình biến môi trường
│   ├── .gitignore               # Cấu hình bỏ qua tệp của backend
│   ├── requirements.txt         # Thư viện phụ thuộc Python
│   └── app/
│       ├── config.py            # Quản lý cài đặt & nạp .env
│       ├── database.py          # Kết nối SQLAlchemy engine & session
│       ├── models.py            # ORM Models (User, Device, Sensor, ...)
│       ├── schemas.py           # Pydantic schemas (Request/Response)
│       ├── mqtt_service.py      # Xử lý Paho MQTT pub/sub
│       ├── seed_mock.py         # Script sinh bản ghi mock data vào DB
│       ├── main.py              # FastAPI app & Lifespan router
│       └── routers/             # API Routers
│           ├── actions.py       # API lịch sử thao tác bật/tắt thiết bị
│           ├── devices.py       # API danh sách & điều khiển thiết bị
│           └── sensors.py       # API danh mục, giá trị mới nhất & lịch sử đo
│
├── frontend/                    # Giao diện Web React + Vite
│   ├── .gitignore               # Cấu hình bỏ qua tệp của frontend
│   ├── package.json             # Khai báo gói phụ thuộc npm
│   ├── vite.config.js           # Cấu hình Vite dev server
│   ├── index.html
│   └── src/
│       ├── App.jsx              # Định tuyến & Bố cục ứng dụng
│       ├── main.jsx             # Entry point
│       ├── index.css            # Style toàn cục
│       ├── api/                 # Axios client & mock adapter
│       ├── components/          # Các component giao diện
│       └── pages/               # Các trang (Dashboard, DataSensor, ActionHistory, Profile)
│
└── esp32/                       # Mã nguồn MicroPython trên ESP32
    ├── secrets.py.example       # Mẫu cấu hình WiFi & MQTT broker
    └── main.py                  # Mã nguồn chính đọc cảm biến & nhận lệnh MQTT
```

---

## 6. Yêu cầu môi trường

- **Python:** 3.10 trở lên
- **Node.js:** 18.x trở lên & **npm:** 9.x trở lên
- **MySQL Server:** 8.0 trở lên
- **MQTT Broker:** Eclipse Mosquitto (hoặc EMQX / HiveMQ)
- **Công cụ nạp vi điều khiển:** Thonny IDE / `mpremote` / `ampy`

---

## 7. Hướng dẫn cài đặt & Khởi chạy

### Bước 1: Khởi tạo Cơ sở dữ liệu (MySQL)
Chạy lần lượt 3 tệp SQL trong thư mục `database/`:
```bash
mysql -u root -p < database/init.sql
mysql -u baonguyenn2302 -p'Bao@23022005' smart_house < database/schema.sql
mysql -u baonguyenn2302 -p'Bao@23022005' smart_house < database/seed.sql
```

### Bước 2: Khởi chạy MQTT Broker
```bash
# Trên macOS:
brew services start mosquitto

# Hoặc khởi chạy kèm log chi tiết:
mosquitto -c /opt/homebrew/etc/mosquitto/mosquitto.conf -v
```

### Bước 3: Cài đặt và Chạy Backend
1. Di chuyển vào thư mục backend và tạo môi trường ảo:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Cài đặt các gói phụ thuộc:
   ```bash
   pip install -r requirements.txt
   ```
3. Cấu hình biến môi trường:
   ```bash
   cp .env.example .env
   # Chỉnh sửa file .env với thông tin kết nối DB và MQTT của bạn
   ```
4. Khởi chạy server FastAPI:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Bước 4: Tạo dữ liệu mẫu (Mock Data Seeding)
Nếu cần dữ liệu để kiểm thử biểu đồ và bảng dữ liệu ngay:
```bash
cd backend
source .venv/bin/activate
python -m app.seed_mock
```

### Bước 5: Cài đặt và Chạy Frontend
1. Mở một terminal mới và di chuyển vào thư mục frontend:
   ```bash
   cd frontend
   npm install
   ```
2. Khởi chạy máy chủ phát triển Vite:
   ```bash
   npm run dev
   ```
3. Mở trình duyệt tại: `http://localhost:5173`

### Bước 6: Cấu hình ESP32
1. Di chuyển vào thư mục `esp32/`:
   ```bash
   cp esp32/secrets.py.example esp32/secrets.py
   ```
2. Cập nhật `WIFI_SSID`, `WIFI_PASSWORD` và IP máy chủ MQTT (`MQTT_BROKER`).
3. Nạp 2 file `secrets.py` và `main.py` vào mạch ESP32.

---

## 8. Danh sách RESTful API

Tài liệu Swagger tương tác trực tiếp có tại: **`http://localhost:8000/docs`**

| Nhóm | Method | Endpoint | Mô tả |
| :--- | :--- | :--- | :--- |
| **System** | `GET` | `/api/health` | Kiểm tra tình trạng backend và kết nối MQTT |
| **Sensors** | `GET` | `/api/sensors` | Lấy danh mục các cảm biến và ngưỡng cảnh báo |
| **Sensors** | `GET` | `/api/sensors/latest` | Lấy giá trị mới nhất của từng cảm biến (Dashboard) |
| **Sensors** | `GET` | `/api/sensors/data` | Lịch sử dữ liệu đo, hỗ trợ tìm kiếm, lọc, phân trang và sắp xếp |
| **Devices** | `GET` | `/api/devices` | Danh sách thiết bị và trạng thái hiện tại |
| **Devices** | `POST` | `/api/devices/{id}/control` | Gửi lệnh bật/tắt thiết bị qua MQTT (`ON`/`OFF`) |
| **Actions** | `GET` | `/api/actions` | Lịch sử thao tác bật/tắt thiết bị (phân trang, lọc theo trạng thái) |

---

## 9. Bảo mật & Quản lý môi trường

- **Không bao giờ commit** các thông tin mật khẩu hoặc cấu hình môi trường lên Git (`.env`, `esp32/secrets.py`).
- Dự án đã cấu hình sẵn `.gitignore` tại root, `backend/` và `frontend/` để ngăn ngừa rò rỉ mã bí mật.
- Luôn sử dụng các file mẫu `.env.example` và `secrets.py.example` khi chia sẻ hoặc triển khai trên máy tính mới.
