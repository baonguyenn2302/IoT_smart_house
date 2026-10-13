import axios from "axios";

export const api = axios.create({ baseURL: "/api" });

// ===== Danh mục =====
const SENSOR_LIST = [
  { id: 1, name: "Temperature", unit: "°C", min_normal: 18, max_normal: 35 },
  { id: 2, name: "Humidity", unit: "%", min_normal: 40, max_normal: 80 },
  { id: 3, name: "Light", unit: "lux", min_normal: 100, max_normal: 800 },
];
const SENSOR_BY_FIELD = { TEMPERATURE: "Temperature", HUMIDITY: "Humidity", LIGHT: "Light" };
const USER = { id: 1, username: "baonguyenn2302", full_name: "Nguyễn Gia Bảo" };
const devices = [
  { id: 1, name: "LED 1", status: "OFF" },
  { id: 2, name: "LED 2", status: "OFF" },
];

// ===== Helper =====
const pad = (n) => String(n).padStart(2, "0");
const round1 = (x) => Math.round(x * 10) / 10;
const fmt = (d) =>
  `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
  `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
// Đổi sang dd/mm/yyyy hh:mm:ss để tìm kiếm theo Time giống backend
const fmtSearch = (iso) => {
  const [d, t] = iso.split("T");
  const [y, m, day] = d.split("-");
  return `${day}/${m}/${y} ${t}`;
};
const paginate = (items, params) => {
  const page = Number(params.page || 1);
  const size = Number(params.size || 10);
  return {
    items: items.slice((page - 1) * size, page * size),
    total: items.length,
    page,
    size,
  };
};

// ===== Dữ liệu cảm biến =====
const dataRows = [];
let tickCount = 0;

function pushMeasurement(date, i) {
  const values = {
    1: 28.5 + Math.sin(i / 5) * 1.2 + Math.random() * 0.3,
    2: 65 + Math.sin(i / 7) * 3 + Math.random(),
    3: 450 + Math.sin(i / 4) * 60 + Math.random() * 20,
  };
  for (const s of SENSOR_LIST) {
    dataRows.push({
      id: dataRows.length + 1,
      value: round1(values[s.id]),
      recorded_at: fmt(date),
      sensor_id: s.id,
      sensor: s,
    });
  }
}

// 120 lần đo lịch sử, mỗi lần cách nhau 2.5 giây
for (let i = 0; i < 120; i++) {
  pushMeasurement(new Date(Date.now() - (120 - i) * 2500), i);
}
tickCount = 120;
let lastTick = Date.now();

// Mỗi lần frontend hỏi dữ liệu mà đã quá 2.5 giây thì sinh thêm một lần đo mới, giống ESP32
function tick() {
  if (Date.now() - lastTick < 2500) return;
  lastTick = Date.now();
  pushMeasurement(new Date(), tickCount++);
}

function latestValues() {
  return SENSOR_LIST.map((s) => {
    const last = [...dataRows].reverse().find((r) => r.sensor_id === s.id);
    const is_normal = last.value >= s.min_normal && last.value <= s.max_normal;
    return { sensor: s, value: last.value, recorded_at: last.recorded_at, is_normal };
  });
}

function queryData(params) {
  let rows = [...dataRows];

  if (params.sensor_id) rows = rows.filter((r) => r.sensor_id === Number(params.sensor_id));
  if (params.from) rows = rows.filter((r) => r.recorded_at >= params.from);
  if (params.to) rows = rows.filter((r) => r.recorded_at <= params.to);

  if (params.q) {
    const q = params.q.toLowerCase();
    const field = params.field || "ALL";
    rows = rows.filter((r) => {
      const name = r.sensor.name.toLowerCase();
      const val = `${r.value}${r.sensor.unit}`.toLowerCase();
      const time = fmtSearch(r.recorded_at);
      if (field === "TIME") return time.includes(q);
      if (field === "ALL") return name.includes(q) || val.includes(q) || time.includes(q);
      return name === SENSOR_BY_FIELD[field].toLowerCase() && val.includes(q);
    });
  }

  const order = {
    TIME_DESC: (a, b) => b.id - a.id,
    TIME_ASC: (a, b) => a.id - b.id,
    VALUE_DESC: (a, b) => b.value - a.value || b.id - a.id,
    VALUE_ASC: (a, b) => a.value - b.value || b.id - a.id,
  };
  rows.sort(order[params.sort || "TIME_DESC"]);

  return paginate(rows, params);
}

// ===== Lịch sử thao tác =====
const actionRows = [];

function addAction(deviceId, action, status, date, user) {
  actionRows.push({
    id: actionRows.length + 1,
    action,
    status,
    recorded_at: fmt(date),
    device: { ...devices[deviceId - 1] },
    user,
  });
}

for (let i = 0; i < 25; i++) {
  const status = i === 24 ? "PENDING" : i % 7 === 4 ? "FAILED" : "SUCCESS";
  addAction(
    (i % 2) + 1,
    i % 3 === 0 ? "OFF" : "ON",
    status,
    new Date(Date.now() - (25 - i) * 60000),
    i % 4 === 0 ? null : USER
  );
}

function queryActions(params) {
  let rows = [...actionRows];
  if (params.device_id) rows = rows.filter((r) => r.device.id === Number(params.device_id));
  if (params.status) rows = rows.filter((r) => r.status === params.status);
  if (params.action) rows = rows.filter((r) => r.action === params.action);
  rows.sort((a, b) => (params.sort === "TIME_ASC" ? a.id - b.id : b.id - a.id));
  return paginate(rows, params);
}

// Bấm bật/tắt: đổi trạng thái LED ngay và ghi lịch sử thành công
function control(deviceId, action) {
  const device = devices.find((d) => d.id === deviceId);
  if (!device) throw new Error("Không tìm thấy thiết bị");
  device.status = action;
  actionRows.push({
    id: actionRows.length + 1,
    action,
    status: "SUCCESS",
    recorded_at: fmt(new Date()),
    device: { ...device },
    user: null,
  });
  return actionRows[actionRows.length - 1];
}

// ===== Bộ định tuyến giả lập =====
function handle(method, url, params, body) {
  if (method === "GET") {
    if (url === "/sensors") return SENSOR_LIST;
    if (url === "/sensors/latest") {
      tick();
      return latestValues();
    }
    if (url === "/sensors/data") {
      tick();
      return queryData(params);
    }
    if (url === "/devices") return devices;
    if (url === "/actions") return queryActions(params);
  }
  const m = url.match(/^\/devices\/(\d+)\/control$/);
  if (method === "POST" && m) return control(Number(m[1]), body.action);
  throw new Error(`Mock chưa hỗ trợ: ${method} ${url}`);
}

// Adapter thay thế cho việc gọi mạng: trả dữ liệu sau 150 ms để giống độ trễ thật
function mockAdapter(config) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      try {
        const method = (config.method || "get").toUpperCase();
        const body = config.data ? JSON.parse(config.data) : undefined;
        const data = handle(method, config.url, config.params || {}, body);
        resolve({ data, status: 200, statusText: "OK", headers: {}, config });
      } catch (e) {
        reject({
          message: e.message,
          response: { status: 400, data: { detail: e.message } },
        });
      }
    }, 150);
  });
}

api.defaults.adapter = mockAdapter;
