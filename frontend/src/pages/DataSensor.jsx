import { useEffect, useState } from "react";
import { ChevronDown, RotateCw, Search } from "lucide-react";
import { api } from "../api/client";
import Pagination from "../components/Pagination";

const SEARCH_FIELDS = [
  { value: "ALL", label: "All" },
  { value: "TIME", label: "Time" },
  { value: "TEMPERATURE", label: "Temperature" },
  { value: "HUMIDITY", label: "Humidity" },
  { value: "LIGHT", label: "Light" },
];

const SORT_OPTIONS = [
  { value: "TIME_DESC", label: "Newest first" },
  { value: "TIME_ASC", label: "Oldest first" },
  { value: "VALUE_DESC", label: "Value: high to low" },
  { value: "VALUE_ASC", label: "Value: low to high" },
];

const DEBOUNCE_MS = 300;

const placeholderFor = (field) =>
  `Search ${SEARCH_FIELDS.find((f) => f.value === field)?.label ?? "All"}...`;

export default function DataSensor() {
  const [field, setField] = useState("ALL");
  const [keyword, setKeyword] = useState("");
  const [debouncedKeyword, setDebouncedKeyword] = useState("");
  const [sort, setSort] = useState("TIME_DESC");
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(10);
  const [data, setData] = useState({ items: [], total: 0 });

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
      .get("/sensors/data", {
        params: {
          q: debouncedKeyword || undefined,
          field,
          sort,
          page,
          size,
        },
      })
      .then((r) => setData(r.data));
  }, [debouncedKeyword, field, sort, page, size]);

  function reset() {
    setField("ALL");
    setKeyword("");
    setDebouncedKeyword("");
    setSort("TIME_DESC");
    setPage(1);
  }

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Data Sensor</h1>
          <p>Real-time sensor data records</p>
        </div>
      </header>

      <div className="filters">
        <label className="control">
          <select
            value={field}
            onChange={(e) => {
              setField(e.target.value);
              setPage(1);
            }}
          >
            {SEARCH_FIELDS.map((f) => (
              <option key={f.value} value={f.value}>
                Search: {f.label}
              </option>
            ))}
          </select>
          <ChevronDown size={14} />
        </label>

        <label className="control search">
          <Search size={16} />
          <input
            placeholder={placeholderFor(field)}
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </label>

        <label className="control">
          <select
            value={sort}
            onChange={(e) => {
              setSort(e.target.value);
              setPage(1);
            }}
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
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
              <th>Name</th>
              <th>Value</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((it) => (
              <tr key={it.id}>
                <td className="id">#{String(it.id).padStart(3, "0")}</td>
                <td>{it.sensor.name}</td>
                <td>
                  {it.value}
                  {it.sensor.unit}
                </td>
                <td>{it.recorded_at.replace("T", " ")}</td>
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
