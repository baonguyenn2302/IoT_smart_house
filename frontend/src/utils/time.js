export const TIME_OPTIONS = [
  { value: "", label: "Mọi thời gian" },
  { value: "1h", label: "1 giờ qua" },
  { value: "24h", label: "24 giờ qua" },
  { value: "7d", label: "7 ngày qua" },
];

const pad = (n) => String(n).padStart(2, "0");

function toLocalIso(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
    `T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

const SPAN_MS = { "1h": 3600e3, "24h": 86400e3, "7d": 7 * 86400e3 };

export function timeRangeParams(value) {
  if (!value) return {};
  return { from: toLocalIso(new Date(Date.now() - SPAN_MS[value])) };
}