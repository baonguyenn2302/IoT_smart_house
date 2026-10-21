import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Cpu, Database, Gauge, History, LogOut, User } from "lucide-react";
import { clearToken } from "../utils/auth";

const links = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/sensors", label: "Data Sensor", icon: Database },
  { to: "/actions", label: "Action History", icon: History },
  { to: "/profile", label: "Profile", icon: User },
];

export default function Layout() {
  const navigate = useNavigate();

  function logout() {
    clearToken();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Cpu size={20} />
          </div>
          <strong>IoT Monitor</strong>
        </div>

        <nav className="nav">
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === "/"}>
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <button className="logout" onClick={logout}>
          <LogOut size={18} />
          Đăng xuất
        </button>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
