const SIZES = [10, 15, 20];

export default function Pagination({ page, size, total, count, onPage, onSize }) {
  const pages = Math.max(1, Math.ceil(total / size));
  return (
    <div className="pager">
      <span>Trang <b>{page}</b> / {pages}</span>
      <span className="count-pill">{count} / {total}</span>
      <div className="size">
        <select value={size} onChange={(e) => onSize(Number(e.target.value))}>
          {SIZES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <span>/ trang</span>
      </div>
      <div className="spacer" />
      <div className="btns">
        <button disabled={page <= 1} onClick={() => onPage(1)}>First</button>
        <button disabled={page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
        <button disabled={page >= pages} onClick={() => onPage(page + 1)}>Next</button>
        <button disabled={page >= pages} onClick={() => onPage(pages)}>Last</button>
      </div>
    </div>
  );
}