import { useState } from "react";
import { Copy, Check } from "lucide-react";

export default function CopyTime({ value }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      alert("Không sao chép được");
    }
  }

  return (
    <span className="time-cell">
      {value}
      <button
        className="copy-btn"
        onClick={copy}
        title="Sao chép thời gian"
        aria-label="Sao chép thời gian"
      >
        {copied ? <Check size={14} /> : <Copy size={14} />}
      </button>
    </span>
  );
}
