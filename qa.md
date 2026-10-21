# 🎯 BỘ CÂU HỎI THỰC HÀNH LIVECODE & VẤN ĐÁP BẢO VỆ ĐỒ ÁN IOT SMART HOUSE

> **Mục đích:** Tài liệu tổng hợp các tình huống thầy cô thường yêu cầu **Livecode tại chỗ (trực tiếp sửa code và chạy thử)** và các câu hỏi **Vấn đáp lý thuyết / Cơ chế hoạt động** của hệ thống Smart House kèm lời giải mẫu chi tiết, nhanh gọn.

---

## 📑 MỤC LỤC
- [PHẦN 1: CÁC BÀI TOÁN LIVECODE THƯỜNG GẶP](#phần-1-các-bài-toán-livecode-thường-gặp)
  - [Livecode 1: Thêm một thiết bị mới (Ví dụ: Thêm Đèn LED 3 hoặc Còi Buzzer)](#livecode-1-thêm-một-thiết-bị-mới-ví-dụ-thêm-đèn-led-3-hoặc-còi-buzzer)
  - [Livecode 2: Thêm nút "Bật tất cả" / "Tắt tất cả" (All ON / All OFF) trên Frontend](#livecode-2-thêm-nút-bật-tất-cả--tắt-tất-cả-all-on--all-off-trên-frontend)
  - [Livecode 3: Đổi màu nền Card cảm biến khi giá trị vượt ngưỡng an toàn](#livecode-3-đổi-màu-nền-card-cảm-biến-khi-giá-trị-vượt-ngưỡng-an-toàn)
  - [Livecode 4: Thay đổi chu kỳ gửi dữ liệu cảm biến từ ESP32](#livecode-4-thay-đổi-chu-kỳ-gửi-dữ-liệu-cảm-biến-từ-esp32)
  - [Livecode 5: Tự động bật đèn khi trời tối (Logic tự động hóa trên ESP32)](#livecode-5-tự-động-bật-đèn-khi-trời-tối-logic-tự-động-hóa-trên-esp32)
  - [Livecode 6: Thay đổi thời gian Timeout xác nhận lệnh điều khiển](#livecode-6-thay-đổi-thời-gian-timeout-xác-nhận-lệnh-điều-khiển)
  - [Livecode 7: Thay đổi số lượng mốc thời gian hiển thị trên biểu đồ Recharts](#livecode-7-thay-đổi-số-lượng-mốc-thời-gian-hiển-thị-trên-biểu-đồ-recharts)
  - [Livecode 8: Viết thêm API thống kê số lần bật/tắt thiết bị](#livecode-8-viết-thêm-api-thống-kê-số-lần-bậttắt-thiết-bị)
- [PHẦN 2: BỘ CÂU HỎI VẤN ĐÁP CƠ CHẾ & KIẾN TRÚC](#phần-2-bộ-câu-hỏi-vấn-đáp-cơ-chế--kiến-trúc)
  - [Câu 1: Tại sao lệnh điều khiển lại cần trạng thái PENDING mà không chốt SUCCESS ngay?](#câu-1-tại-sao-lệnh-điều-khiển-lại-cần-trạng-thái-pending-mà-không-chốt-success-ngay)
  - [Câu 2: Tại sao Backend dùng loop_start() của Paho MQTT mà không dùng loop_forever()?](#câu-2-tại-sao-backend-dùng-loop_start-của-paho-mqtt-mà-không-dùng-loop_forever)
  - [Câu 3: Đồ án đang sử dụng MQTT QoS mức mấy? Ưu nhược điểm là gì?](#câu-3-đồ-án-đang-sử-dụng-mqtt-qos-mức-mấy-ưu-nhược-điểm-là-gì)
  - [Câu 4: Tại sao trong CSDL lại đánh Index phức hợp trên (sensor_id, recorded_at)?](#câu-4-tại-sao-trong-csdl-lại-đánh-index-phức-hợp-trên-sensor_id-recorded_at)
  - [Câu 5: Nếu mất mạng WiFi hoặc mất Broker, mạch ESP32 xử lý như thế nào?](#câu-5-nếu-mất-mạng-wifi-hoặc-mất-broker-mạch-esp32-xử-lý-như-thế-nào)
  - [Câu 6: Cơ chế get_db() trong FastAPI đóng mở kết nối database ra sao?](#câu-6-cơ-chế-get_db-trong-fastapi-đóng-mở-kết-nối-database-ra-sao)

---

# PHẦN 1: CÁC BÀI TOÁN LIVECODE THƯỜNG GẶP

---

### Livecode 1: Thêm một thiết bị mới (Ví dụ: Thêm Đèn LED 3 hoặc Còi Buzzer)
**Đề bài của thầy cô:** *"Hiện tại hệ thống đang có 2 LED. Giờ em hãy thêm LED 3 (chân GPIO 27) vào hệ thống để có thể bật/tắt được từ Web."*

#### Các file cần sửa:
1. `database/seed.sql` (hoặc chạy lệnh SQL chèn vào DB)
2. `esp32/main.py`
3. `backend/app/schemas.py`
4. `backend/app/mqtt_service.py`

#### Cách xử lý:
- **Bước 1: Chèn vào Database (MySQL)**
  Chạy lệnh trong MySQL:
  ```sql
  INSERT INTO devices (id, name, status) VALUES (3, 'LED 3', 'OFF');
  ```
- **Bước 2: Cập nhật `esp32/main.py`**
  ```python
  # Thêm chân GPIO 27
  LED3_PIN = 27
  led3 = Pin(LED3_PIN, Pin.OUT)

  # Trong hàm gui_trang_thai_led():
  def gui_trang_thai_led():
      trang_thai = '{{"led1": "{}", "led2": "{}", "led3": "{}"}}'.format(
          "on" if led1.value() == 1 else "off",
          "on" if led2.value() == 1 else "off",
          "on" if led3.value() == 1 else "off",
      )
      client.publish(TOPIC_RESPONSE, trang_thai)

  # Trong hàm xu_ly_lenh():
  elif lenh == "led3:on":
      led3.value(1)
  elif lenh == "led3:off":
      led3.value(0)
  ```
- **Bước 3: Cập nhật `backend/app/schemas.py`**
  ```python
  class DeviceStatusPayload(BaseModel):
      led1: Optional[DeviceStatus] = None
      led2: Optional[DeviceStatus] = None
      led3: Optional[DeviceStatus] = None  # <-- Thêm dòng này

      @field_validator("led1", "led2", "led3", mode="before")  # <-- Thêm "led3" vào validator
      @classmethod
      def normalize(cls, value):
          if isinstance(value, str):
              return value.strip().upper()
          return value
  ```
- **Bước 4: Cập nhật `backend/app/mqtt_service.py`**
  ```python
  DEVICE_NAME_TO_KEY = {
      "LED 1": "led1",
      "LED 2": "led2",
      "LED 3": "led3",  # <-- Thêm dòng này
  }
  ```
- **Kết quả:** Vì Frontend tự động gọi API `GET /api/devices` lấy danh sách động, nên ngay khi chèn vào DB và khai báo ở Backend, nút switch của **LED 3** sẽ tự động xuất hiện trên giao diện Web Dashboard!

---

### Livecode 2: Thêm nút "Bật tất cả" / "Tắt tất cả" (All ON / All OFF) trên Frontend
**Đề bài của thầy cô:** *"Thêm 2 nút bấm trên giao diện Dashboard để một phát bật hết hoặc tắt hết cả 2 đèn."*

#### Các file cần sửa:
- `frontend/src/pages/Dashboard.jsx` (Lưu ý: trong `esp32/main.py` đã có sẵn lệnh `all:on` và `all:off`).

#### Cách xử lý:
Thêm hàm xử lý và 2 nút bấm trong `frontend/src/pages/Dashboard.jsx`:

```jsx
// 1. Thêm hàm xử lý bật/tắt toàn bộ
async function handleToggleAll(action) {
  try {
    for (const d of devices) {
      await api.post(`/devices/${d.id}/control`, { action });
    }
  } catch (err) {
    console.error("Lỗi điều khiển tất cả:", err);
  }
}

// 2. Thêm JSX 2 nút bấm vào ngay trên khu vực danh sách thiết bị
<div style={{ display: "flex", gap: "10px", marginBottom: "15px" }}>
  <button 
    className="btn-primary" 
    style={{ background: "#22c55e" }}
    onClick={() => handleToggleAll("ON")}
  >
    Bật tất cả
  </button>
  <button 
    className="btn-primary" 
    style={{ background: "#ef4444" }}
    onClick={() => handleToggleAll("OFF")}
  >
    Tắt tất cả
  </button>
</div>
```

---

### Livecode 3: Đổi màu nền Card cảm biến khi giá trị vượt ngưỡng an toàn
**Đề bài của thầy cô:** *"Khi nhiệt độ hoặc độ ẩm bất thường (vượt max_normal hoặc nhỏ hơn min_normal), hãy đổi màu nền hoặc viền thẻ cảm biến sang màu đỏ để cảnh báo."*

#### File cần sửa:
- `frontend/src/pages/Dashboard.jsx`

#### Cách xử lý:
Mở `frontend/src/pages/Dashboard.jsx`, tìm tới đoạn render `sensor-cards`:

```jsx
<section className="sensor-cards">
  {latest.map((s) => {
    const Icon = ICON_BY_SENSOR[s.sensor.name] ?? Sun;
    const isBad = s.is_normal === false; // <-- Kiểm tra nếu vượt ngưỡng

    return (
      <div 
        className="card sensor-card" 
        key={s.sensor.id}
        // Thêm style đổi màu viền/nền khi bị bất thường:
        style={isBad ? { borderColor: "#ef4444", backgroundColor: "#fef2f2" } : {}}
      >
        <div className="sensor-head">
          <span className="sensor-label">
            <Icon size={18} />
            {s.sensor.name}
          </span>
          {isBad && (
            <span style={{ color: "#ef4444", fontSize: "12px", fontWeight: "bold" }}>
              ⚠️ Vượt ngưỡng!
            </span>
          )}
        </div>
        <div className="sensor-value">
          {s.value === null ? "--" : `${s.value} ${s.sensor.unit ?? ""}`}
        </div>
      </div>
    );
  })}
</section>
```

---

### Livecode 4: Thay đổi chu kỳ gửi dữ liệu cảm biến từ ESP32
**Đề bài của thầy cô:** *"Hiện tại cảm biến gửi 2.5 giây/lần. Hãy chỉnh thành 5 giây gửi 1 lần hoặc 10 giây gửi 1 lần."*

#### File cần sửa:
- `esp32/main.py`

#### Cách xử lý:
Tìm đến vòng lặp vô tận ở cuối file:
```python
lan_thu = 1
while True:
    try:
        client.check_msg()

        # Mỗi vòng lặp ngủ 0.5s:
        # Nếu muốn 5 giây: 5s / 0.5s = 10 vòng lặp -> lan_thu % 10 == 0
        # Nếu muốn 10 giây: 10s / 0.5s = 20 vòng lặp -> lan_thu % 20 == 0
        if lan_thu % 10 == 0:  # <-- Đổi 5 thành 10 (tương ứng 5 giây)
            doc_va_gui_cam_bien()

        lan_thu += 1
    except OSError as e:
        khoi_phuc_ket_noi()

    time.sleep(0.5)
```

---

### Livecode 5: Tự động bật đèn khi trời tối (Logic tự động hóa trên ESP32)
**Đề bài của thầy cô:** *"Hãy lập trình để khi cảm biến ánh sáng đọc được lux < 100 thì tự bật LED 1, khi lux >= 100 thì tự tắt LED 1."*

#### File cần sửa:
- `esp32/main.py`

#### Cách xử lý:
Thêm logic điều khiển tự động ngay trong hàm `doc_va_gui_cam_bien()`:

```python
def doc_va_gui_cam_bien():
    # ... (đo nhiệt độ, lux)
    try:
        lux = bh1750_read_lux()
    except OSError as e:
        lux = None

    # === THÊM LOGIC TỰ ĐỘNG BẬT ĐÈN THEO ÁNH SÁNG ===
    if lux is not None:
        if lux < 100:
            if led1.value() != 1:
                led1.value(1)
                gui_trang_thai_led()  # Báo ngay về server trạng thái đã bật
        else:
            if led1.value() != 0:
                led1.value(0)
                gui_trang_thai_led()  # Báo ngay về server trạng thái đã tắt
    # ===============================================

    # ... (publish payload lên TOPIC_SENSOR)
```

---

### Livecode 6: Thay đổi thời gian Timeout xác nhận lệnh điều khiển
**Đề bài của thầy cô:** *"Giảm thời gian chờ phản hồi của ESP32 từ 5s xuống 3s, hoặc tăng lên 10s."*

#### Các file cần sửa:
1. `backend/app/mqtt_service.py`:
   ```python
   ACK_TIMEOUT_SECONDS = 3  # Đổi từ 5 thành 3 (hoặc 10)
   ```
2. `frontend/src/pages/Dashboard.jsx`:
   ```javascript
   const PENDING_MS = 3000; // Đổi tương ứng với backend (3s = 3000ms)
   ```

---

### Livecode 7: Thay đổi số lượng mốc thời gian hiển thị trên biểu đồ Recharts
**Đề bài của thầy cô:** *"Biểu đồ đang hiển thị 10 điểm đo gần nhất, hãy đổi thành 20 điểm đo."*

#### File cần sửa:
- `frontend/src/pages/Dashboard.jsx`:

```javascript
// Dòng 16:
const POINTS = 20; // <-- Đổi từ 10 thành 20

// Trong hàm loadSensors():
// Muốn hiển thị 20 điểm thì cần ít nhất 20 * 3 cảm biến = 60 bản ghi trở lên
api.get("/sensors/data", { params: { size: 90 } }) // <-- Đổi size từ 60 lên 90 hoặc 120
```

---

### Livecode 8: Viết thêm API thống kê số lần bật/tắt thiết bị
**Đề bài của thầy cô:** *"Viết thêm 1 endpoint GET `/api/actions/summary` trả về tổng số lần thao tác thành công, thất bại và đang chờ."*

#### File cần sửa:
- `backend/app/routers/actions.py`

#### Cách xử lý:
Thêm đoạn code sau vào cuối file `backend/app/routers/actions.py`:

```python
@router.get("/summary", summary="Thống kê trạng thái lệnh")
def get_action_summary(db: Session = Depends(get_db)):
    success_count = db.scalar(
        select(func.count(ActionHistory.id)).where(ActionHistory.status == ActionStatus.SUCCESS)
    )
    failed_count = db.scalar(
        select(func.count(ActionHistory.id)).where(ActionHistory.status == ActionStatus.FAILED)
    )
    pending_count = db.scalar(
        select(func.count(ActionHistory.id)).where(ActionHistory.status == ActionStatus.PENDING)
    )
    return {
        "success": success_count or 0,
        "failed": failed_count or 0,
        "pending": pending_count or 0,
        "total": (success_count or 0) + (failed_count or 0) + (pending_count or 0)
    }
```
*Truy cập thử ngay tại: `http://localhost:8000/docs` để kiểm tra kết quả.*

---

# PHẦN 2: BỘ CÂU HỎI VẤN ĐÁP CƠ CHẾ & KIẾN TRÚC

---

### Câu 1: Tại sao lệnh điều khiển lại cần trạng thái PENDING mà không chốt SUCCESS ngay?
- **Trả lời:** 
  - Trong hệ thống IoT thực tế, mạng không dây và thiết bị phần cứng có thể gặp sự cố (mất nguồn, đứt dây, mất WiFi, lỗi Broker).
  - Nếu vừa bấm nút trên Web mà đánh dấu `SUCCESS` và đổi trạng thái đèn thành `ON` ngay lập tức thì sẽ gây ra hiện tượng **"sai lệch thực tế"** (trên Web báo đèn sáng nhưng bóng đèn thực tế vẫn tắt).
  - Do đó, hệ thống áp dụng cơ chế **xác nhận 2 chiều (Two-way Confirmation)**:
    1. Web gửi lệnh ➔ Backend lưu `PENDING` và bắn lệnh qua MQTT.
    2. ESP32 thực sự kích chân GPIO xong ➔ gửi phản hồi báo lại qua topic `/devices/status`.
    3. Backend nhận được phản hồi mới chuyển sang `SUCCESS`.
    4. Nếu sau 5 giây không có phản hồi, Backend tự chuyển sang `FAILED`.

---

### Câu 2: Tại sao Backend dùng `loop_start()` của Paho MQTT mà không dùng `loop_forever()`?
- **Trả lời:**
  - `loop_forever()` là hàm **chặn (blocking call)**, nó sẽ chiếm hoàn toàn luồng chính của tiến trình. Nếu gọi `loop_forever()`, máy chủ FastAPI / Uvicorn sẽ bị treo và không thể tiếp nhận các request HTTP từ người dùng.
  - `loop_start()` sẽ tự động khởi tạo một **luồng phụ chạy ngầm (background thread)** chuyên trách việc duy trì kết nối mạng MQTT, gửi keepalive ping và nhận message bất đồng bộ, giúp máy chủ FastAPI tiếp tục chạy luồng chính để phục vụ các RESTful API mà không bị ảnh hưởng.

---

### Câu 3: Đồ án đang sử dụng MQTT QoS mức mấy? Ưu nhược điểm là gì?
- **Trả lời:**
  - Hệ thống đang dùng **QoS 0 (At most once - Gửi tối đa một lần)**.
  - **Ưu điểm:** Tốc độ truyền tin nhanh nhất, độ trễ cực thấp, không tốn tài nguyên bộ nhớ và băng thông của ESP32 (rất phù hợp cho việc truyền dữ liệu cảm biến định kỳ liên tục mỗi 2.5s - nếu mất 1 gói thì 2.5s sau sẽ có gói mới bù vào).
  - **Nhược điểm:** Không có cơ chế bắt tay đảm bảo gói tin chắc chắn tới đích (nếu mạng chập chờn gói tin có thể bị rơi). 
  - *Mẹo trả lời mở rộng:* Nếu thầy cô hỏi cách nâng cao độ tin cậy cho lệnh bật/tắt thiết bị quan trọng, em có thể nâng QoS lên **QoS 1 (At least once)** kèm cờ `retain=False` để đảm bảo lệnh luôn được giao đến Broker.

---

### Câu 4: Tại sao trong CSDL lại đánh Index phức hợp trên `(sensor_id, recorded_at)`?
- **Trả lời:**
  - Trên giao diện Dashboard và Data Sensor, câu truy vấn thường xuyên nhất là: *"Lấy giá trị của cảm biến X theo thứ tự thời gian mới nhất"* (câu lệnh SQL: `WHERE sensor_id = ? ORDER BY recorded_at DESC LIMIT ?`).
  - Đánh Index phức hợp `(sensor_id, recorded_at)` theo thứ tự này giúp MySQL tìm trực tiếp vào đúng nhóm dữ liệu của cảm biến đó và lấy ngay các bản ghi theo thứ tự thời gian định sẵn mà **không phải quét toàn bộ bảng (Full Table Scan)** và **không cần tốn bộ nhớ để sắp xếp (Avoid Filesort)**, giúp thời gian phản hồi API luôn đạt dưới 10ms kể cả khi bảng có hàng triệu dòng.

---

### Câu 5: Nếu mất mạng WiFi hoặc mất Broker, mạch ESP32 xử lý như thế nào?
- **Trả lời:**
  - Trong `esp32/main.py`, toàn bộ quá trình đọc tin và gửi cảm biến được bọc trong khối `try...except OSError`.
  - Khi mất kết nối, exception sẽ được kích hoạt và chuyển ngay vào hàm `khoi_phuc_ket_noi()`.
  - Hàm này chạy vòng lặp lặp lại việc kiểm tra WiFi, reconnect và kết nối lại MQTT Broker cứ mỗi 3 giây.
  - Ngay khi có mạng trở lại, ESP32 sẽ subscribe lại topic điều khiển và chủ động gọi hàm `gui_trang_thai_led()` để đồng bộ trạng thái thực tế hiện tại của các bóng đèn lên hệ thống.

---

### Câu 6: Cơ chế `get_db()` trong FastAPI đóng mở kết nối database ra sao?
- **Trả lời:**
  - Hàm `get_db()` sử dụng cú pháp `yield` đóng vai trò là một **Dependency Injection** có tính năng dọn dẹp tài nguyên.
  - Khi một HTTP request gửi đến endpoint, FastAPI gọi `get_db()`: một phiên làm việc `SessionLocal()` được tạo ra từ Connection Pool.
  - `yield db` chuyển session này vào hàm xử lý endpoint.
  - Sau khi endpoint xử lý xong (kể cả khi xảy ra lỗi Exception), khối `finally: db.close()` chắc chắn sẽ được thực thi để đóng session và trả kết nối về Connection Pool, đảm bảo **không bao giờ bị rò rỉ kết nối (Connection Leak)** làm cạn kiệt tài nguyên của MySQL Server.
