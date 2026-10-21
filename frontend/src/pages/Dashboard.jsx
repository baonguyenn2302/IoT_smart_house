import { useCallback, useEffect, useRef, useState } from "react";
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Droplet, Lightbulb, Sun, Thermometer } from "lucide-react";
import { api } from "../api/client";

const SENSOR_POLL_MS = 3000;
const DEVICE_POLL_MS = 1000;
const PENDING_MS = 5000; // khớp với ACK_TIMEOUT_SECONDS ở backend
const POINTS = 10; // số thời điểm hiển thị trên mỗi biểu đồ

const KEY_BY_SENSOR = {
  Temperature: "temperature",
  Humidity: "humidity",
  Light: "light",
};
const ICON_BY_SENSOR = {
  Temperature: Thermometer,
  Humidity: Droplet,
  Light: Sun,
};

const AXIS_TICK = { fontSize: 11, fill: "#6b7280" };
const AXIS_LINE = { stroke: "#d1d5db" };

// Gom 3 bản ghi cùng một lần đo thành một điểm trên biểu đồ
function toSeries(items) {
  const map = new Map();
  for (const it of items) {
    const t = it.recorded_at;
    if (!map.has(t)) map.set(t, { time: t.slice(11, 19) });
    map.get(t)[KEY_BY_SENSOR[it.sensor.name]] = it.value;
  }
  // Map giữ thứ tự mới nhất trước: lấy POINTS thời điểm đầu, rồi đảo lại cho biểu đồ chạy từ cũ đến mới
  return [...map.values()].slice(0, POINTS).reverse();
}

// Mốc 200-1000; nếu có giá trị lux vượt 1000 thì thêm chính giá trị đó làm mốc trên cùng. Không có mốc 0.
function buildLuxAxis(maxValue) {
  const base = [200, 400, 600, 800, 1000];
  const ticks = maxValue > 1000 ? [...base, maxValue] : base;
  return { top: Math.max(1000, maxValue), ticks };
}

function Legend({ items }) {
  return (
    <div className="chart-legend">
      {items.map(([color, label]) => (
        <span key={label}>
          <i style={{ background: color }} />
          {label}
        </span>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [latest, setLatest] = useState([]);
  const [devices, setDevices] = useState([]);
  const [series, setSeries] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  // Trạng thái đang chờ ESP32 xác nhận: { [deviceId]: { status, until } }
  const pendingRef = useRef({});

  const loadSensors = useCallback(async () => {
    try {
      // 60 bản ghi = 20 lần đo (3 cảm biến mỗi lần), đủ để luôn có POINTS thời điểm
      const [l, s] = await Promise.all([
        api.get("/sensors/latest"),
        api.get("/sensors/data", { params: { size: 60 } }),
      ]);
      setLatest(l.data);
      setSeries(toSeries(s.data.items));
      setError("");
    } catch {
      setError("Mất kết nối");
    }
  }, []);

  const loadDevices = useCallback(async () => {
    try {
      const { data } = await api.get("/devices");
      const now = Date.now();
      setDevices(
        data.map((d) => {
          const p = pendingRef.current[d.id];
          if (!p) return d;
          // ESP32 đã xác nhận, hoặc đã hết thời gian chờ: dùng dữ liệu từ server
          if (d.status === p.status || now > p.until) {
            delete pendingRef.current[d.id];
            return d;
          }
          // Server chưa cập nhật kịp: giữ trạng thái vừa bấm
          return { ...d, status: p.status };
        }),
      );
    } catch {
      setError("Mất kết nối");
    }
  }, []);

  useEffect(() => {
    loadSensors();
    loadDevices();
    const sensorTimer = setInterval(loadSensors, SENSOR_POLL_MS);
    const deviceTimer = setInterval(loadDevices, DEVICE_POLL_MS);
    return () => {
      clearInterval(sensorTimer);
      clearInterval(deviceTimer);
    };
  }, [loadSensors, loadDevices]);

  async function toggle(device) {
    const action = device.status === "ON" ? "OFF" : "ON";

    // Đổi công tắc ngay, không chờ ESP32
    pendingRef.current[device.id] = {
      status: action,
      until: Date.now() + PENDING_MS,
    };
    setDevices((prev) =>
      prev.map((d) => (d.id === device.id ? { ...d, status: action } : d)),
    );

    setBusyId(device.id);
    try {
      await api.post(`/devices/${device.id}/control`, { action });
    } catch (e) {
      // Lệnh không gửi được: quay về trạng thái thật
      delete pendingRef.current[device.id];
      alert(e.response?.data?.detail ?? "Lỗi điều khiển");
      loadDevices();
    } finally {
      setBusyId(null);
    }
  }

  const luxValues = series.map((p) => p.light).filter((v) => v != null);
  const luxMax = luxValues.length ? Math.max(...luxValues) : 0;
  const lux = buildLuxAxis(luxMax);

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>Real-time sensor monitoring</p>
        </div>
        <span className={`status-pill ${error ? "bad" : ""}`}>
          {error || "System Online"}
        </span>
      </header>

      <section className="sensor-cards">
        {latest.map((s) => {
          const Icon = ICON_BY_SENSOR[s.sensor.name] ?? Sun;
          const normal = s.is_normal !== false;
          return (
            <div className="card sensor-card" key={s.sensor.id}>
              <div className="sensor-head">
                <span className="sensor-label">
                  <Icon size={18} />
                  {s.sensor.name}
                </span>
                {/* Thẻ hiển thị trạng thái Normal / Abnormal (Bỏ comment khi cần sử dụng lại)
                <span className={`badge ${normal ? "good" : "bad"}`}>
                  {s.is_normal === null ? "--" : normal ? "Normal" : "Abnormal"}
                </span>
                */}
              </div>
              <div className="sensor-value">
                {s.value === null ? "--" : `${s.value} ${s.sensor.unit ?? ""}`}
              </div>
            </div>
          );
        })}
      </section>

      <section className="charts">
        <div className="card">
          <div className="chart-head">
            <h3>Temperature &amp; Humidity</h3>
            <Legend
              items={[
                ["#f97316", "Temperature (°C)"],
                ["#2563eb", "Humidity (%)"],
              ]}
            />
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart
              data={series}
              margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
            >
              {/* <XAxis
                dataKey="time"
                tick={AXIS_TICK}
                tickLine={false}
                axisLine={AXIS_LINE}
              /> */}
              <XAxis
                dataKey="time"
                interval={0}
                angle={-30}
                height={50}
                tickMargin={10}
                tick={{ fontSize: 10, fill: "#6b7280" }}
                tickLine={false}
                axisLine={AXIS_LINE}
              />
              <YAxis
                domain={[0, 100]}
                ticks={[20, 40, 60, 80, 100]}
                tick={AXIS_TICK}
                tickLine={false}
                axisLine={AXIS_LINE}
              />
              <Tooltip
                formatter={(value, name) => [Number(value).toFixed(1), name]}
              />
              <Line
                type="monotone"
                dataKey="temperature"
                name="Temperature (°C)"
                stroke="#f97316"
                strokeWidth={2}
                dot={{ r: 3, fill: "#f97316" }}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="humidity"
                name="Humidity (%)"
                stroke="#2563eb"
                strokeWidth={2}
                dot={{ r: 3, fill: "#2563eb" }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="chart-head">
            <h3>Light Intensity</h3>
            <Legend items={[["#22c55e", "Light (lux)"]]} />
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart
              data={series}
              margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
            >
              <XAxis
                dataKey="time"
                interval={0}
                angle={-30}
                height={50}
                tickMargin={10}
                tick={AXIS_TICK}
                tickLine={false}
                axisLine={AXIS_LINE}
              />
              <YAxis
                domain={[0, lux.top]}
                ticks={lux.ticks}
                tick={AXIS_TICK}
                tickLine={false}
                axisLine={AXIS_LINE}
              />
              <Tooltip
                formatter={(value, name) => [Number(value).toFixed(1), name]}
              />
              <Line
                type="monotone"
                dataKey="light"
                name="Light (lux)"
                stroke="#22c55e"
                strokeWidth={2}
                dot={{ r: 3, fill: "#22c55e" }}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="card led-section">
        <h3>LED Control</h3>
        <div className="led-grid">
          {devices.map((d) => {
            const on = d.status === "ON";
            return (
              <div className="led-card" key={d.id}>
                <div className={`led-icon ${on ? "on" : ""}`}>
                  <Lightbulb size={20} />
                </div>
                <div className="led-info">
                  <strong>{d.name}</strong>
                  <span className={on ? "on-text" : "off-text"}>
                    {d.status}
                  </span>
                </div>
                <button
                  role="switch"
                  aria-checked={on}
                  aria-label={`Bật tắt ${d.name}`}
                  className={`switch ${on ? "on" : ""}`}
                  disabled={busyId === d.id}
                  onClick={() => toggle(d)}
                >
                  <span />
                </button>
              </div>
            );
          })}
        </div>
      </section>
    </>
  );
}
