import axios from "axios";
import { getToken, clearToken } from "../utils/auth";

export const api = axios.create({ baseURL: "/api" });

// Gắn token vào mọi request
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Token hết hạn hoặc sai: xóa token và về trang đăng nhập
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && !window.location.pathname.startsWith("/login")) {
      clearToken();
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);