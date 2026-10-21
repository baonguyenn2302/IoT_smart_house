import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Cpu } from "lucide-react";
import { api } from "../api/client";
import { setToken } from "../utils/auth";

export default function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      // Backend dùng OAuth2 form nên gửi dạng form-urlencoded
      const form = new URLSearchParams({ username, password });
      const { data } = await api.post("/auth/login", form);
      setToken(data.access_token);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail ?? "Không kết nối được server");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <div className="login-brand">
          <div className="brand-icon">
            <Cpu size={22} />
          </div>
          <strong>IoT Monitor</strong>
        </div>

        <label className="login-field">
          <span>Tên đăng nhập</span>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </label>

        <label className="login-field">
          <span>Mật khẩu</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>

        {error && <div className="form-error">{error}</div>}

        <button className="btn-primary login-submit" disabled={loading}>
          {loading ? "Đang đăng nhập..." : "Đăng nhập"}
        </button>
      </form>
    </div>
  );
}
