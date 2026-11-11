import { useEffect, useState } from "react";
import { GitBranch, Palette, FileText } from "lucide-react";
import { api } from "../api/client";

// File PDF được phục vụ từ frontend/public/docs.
const DEFAULT_LINKS = {
  report_pdf: "/docs/SRS_IoT_B23DCCN075.pdf",
};

const RESOURCE_META = [
  {
    key: "github",
    title: "GitHub Repository",
    desc: "Source code of the Web IoT project",
    label: "Open GitHub",
    icon: GitBranch,
  },
  {
    key: "figma",
    title: "Figma Design",
    desc: "UI/UX design specification and prototypes",
    label: "Open Figma",
    icon: Palette,
  },
  {
    key: "report_pdf",
    title: "Project Documentation",
    desc: "Software Requirement Specification (SRS) document",
    label: "Download PDF",
    icon: FileText,
    download: true,
    fileName: "STS_Iot_B23DCCN075.pdf",
  },
];

export default function Profile() {
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");
  const [avatarOk, setAvatarOk] = useState(true);

  useEffect(() => {
    api
      .get("/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => setError("Không tải được hồ sơ"));
  }, []);

  if (error) return <p>{error}</p>;
  if (!user) return <p>Đang tải...</p>;

  const FIELDS = [
    ["Full Name", user.full_name],
    ["Student ID", user.student_id],
    ["Class", user.class_name],
    ["Faculty", user.faculty],
    ["Phone Number", user.phone],
    ["Email Address", user.email],
  ];

  const initial = (user.full_name ?? "?").split(" ").pop().charAt(0);

  return (
    <>
      <header className="page-header">
        <div>
          <h1>Profile</h1>
          <p>User information and project resources</p>
        </div>
      </header>

      <section className="card">
        <div className="profile-head">
          {avatarOk ? (
            <img
              className="avatar"
              src="/avatar.jpg"
              alt={user.full_name}
              onError={() => setAvatarOk(false)}
            />
          ) : (
            <div className="avatar">{initial}</div>
          )}
          <div>
            <div className="profile-name">{user.full_name}</div>
            <span className="role">Student / Developer</span>
          </div>
        </div>

        <div className="profile-grid">
          {FIELDS.map(([label, value]) => (
            <div className="field" key={label}>
              <label>{label}</label>
              <input value={value ?? ""} readOnly />
            </div>
          ))}
        </div>
      </section>

      <h2 className="section-title">Project Resources</h2>
      <section className="resource-grid">
        {RESOURCE_META.map(
          ({ key, title, desc, label, icon: Icon, download, fileName }) => {
            // PDF phải dùng file local vì link cũ trong hồ sơ trỏ đến /srs.pdf không tồn tại.
            const href =
              key === "report_pdf"
                ? DEFAULT_LINKS.report_pdf
                : user.links?.[key] || "#";
            return (
              <div className="card resource" key={key}>
                <div className="resource-head">
                  <div className="resource-icon">
                    <Icon size={18} />
                  </div>
                  <strong>{title}</strong>
                </div>
                <p>{desc}</p>
                <a
                  className="btn-primary"
                  href={href}
                  download={download ? fileName : undefined}
                  target={download ? undefined : "_blank"}
                  rel="noreferrer"
                >
                  {label}
                </a>
              </div>
            );
          },
        )}
      </section>
    </>
  );
}
