import { useEffect, useState } from "react";
import { ChevronDown, RotateCw, Search } from "lucide-react";
import { api } from "../api/client";
import CopyTime from "../components/CopyTime";
import Pagination from "../components/Pagination";

const SORT_OPTIONS = [
  { value: "TIME_DESC", label: "Newest first" },
  { value: "TIME_ASC", label: "Oldest first" },
];

const STATUS_LABEL = {
  SUCCESS: "Success",
  PENDING: "Pending",
  FAILED: "Failed",
};
const DEBOUNCE_MS = 300;

export default function ActionHistory() {
  const [devices, setDevices] = useState([]);
  const [keyword, setKeyword] = useState("");
  const [debouncedKeyword, setDebouncedKeyword] = useState("");
  const [sort, setSort] = useState(""); // "" nghĩa là dùng mặc định của API (mới nhất trước)
  const [deviceId, setDeviceId] = useState("");
  const [status, setStatus] = useState("");
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [data, setData] = useState({ items: [], total: 0 });

  useEffect(() => {
    api.get("/devices").then((r) => setDevices(r.data));
  }, []);

  // Chờ người dùng ngừng gõ rồi mới gọi API
  useEffect(() => {
    const id = setTimeout(() => {
      setDebouncedKeyword(keyword);
      setPage(1);
    }, DEBOUNCE_MS);
    return () => clearTimeout(id);
  }, [keyword]);

  useEffect(() => {
    api
      .get("/actions", {
        params: {
          q: debouncedKeyword || undefined,
          device_id: deviceId || undefined,
          status: status || undefined,
          action: action || undefined,
          sort: sort || undefined,
          page,
          size,
        },
      })
      .then((r) => setData(r.data));
  }, [debouncedKeyword, deviceId, status, action, sort, page, size]);

  function handleSortChange(e) {
    setSort(e.target.value);
    setPage(1);
  }

  const withReset = (setter) => (e) => {
    setter(e.target.value);
    setPage(1);
  };

  function reset() {
    setKeyword("");
    setDebouncedKeyword("");
    setSort("");
    setDeviceId("");
    setStatus("");
    setAction("");
    setPage(1);
  }

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Action History</h1>
          <p>Real-time device activity records</p>
        </div>
      </header>

      <div className="filters">
        <label className="control search">
          <Search size={16} />
          <input
            placeholder="Search action history..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </label>

        <label className="control">
          <select value={sort} onChange={handleSortChange}>
            <option value="" disabled>
              Sorted by Date/Time
            </option>
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          <ChevronDown size={14} />
        </label>

        <label className="control">
          <select value={deviceId} onChange={withReset(setDeviceId)}>
            <option value="">Device</option>
            {devices.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <ChevronDown size={14} />
        </label>

        <label className="control">
          <select value={status} onChange={withReset(setStatus)}>
            <option value="">Action Status</option>
            <option value="SUCCESS">Success</option>
            <option value="PENDING">Pending</option>
            <option value="FAILED">Failed</option>
          </select>
          <ChevronDown size={14} />
        </label>

        <label className="control">
          <select value={action} onChange={withReset(setAction)}>
            <option value="">Action</option>
            <option value="ON">ON</option>
            <option value="OFF">OFF</option>
          </select>
          <ChevronDown size={14} />
        </label>

        <button className="control ghost" onClick={reset}>
          <RotateCw size={15} /> Reset
        </button>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Device</th>
              <th>Action</th>
              <th>Actor</th>
              <th>Action Status</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((it) => (
              <tr key={it.id}>
                <td className="id">#{String(it.id).padStart(3, "0")}</td>
                <td>{it.device.name}</td>
                <td>
                  <span className={`tag ${it.action === "ON" ? "on" : ""}`}>
                    {it.action}
                  </span>
                </td>
                <td>{it.user?.full_name ?? "Hệ thống"}</td>
                <td>
                  <span className={`tag ${it.status.toLowerCase()}`}>
                    {STATUS_LABEL[it.status]}
                  </span>
                </td>
                <td>
                  <CopyTime value={it.recorded_at.replace("T", " ")} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination
        page={page}
        size={size}
        total={data.total}
        count={data.items.length}
        onPage={setPage}
        onSize={(s) => {
          setSize(s);
          setPage(1);
        }}
      />
    </>
  );
}
