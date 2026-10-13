import { useState } from "react";
import { GitBranch, Palette, FileText } from "lucide-react";

const PROFILE = {
  full_name: "Nguyễn Gia Bảo",
  student_id: "B23DCCN075",
  class_name: "D23CNPM03",
  faculty: "Information Technology 1",
  phone: "0912825535",
  email: "baonguyenn.contact@gmail.com",
};

const RESOURCES = [
    {
    title: "GitHub Repository",
    desc: "Source code of the Web IoT project",
    label: "Open GitHub",
    icon: GitBranch,
    href: "https://github.com/your-username/smart_house",
  },
  {
    title: "Figma Design",
    desc: "UI/UX design specification and prototypes",
    label: "Open Figma",
    icon: Palette,
    href: "https://www.figma.com/",
  },
  {
    title: "Project Documentation",
    desc: "Software Requirement Specification (SRS) document",
    label: "Download PDF",
    icon: FileText,
    href: "/srs.pdf",
    download: true,
  },
];

const FIELDS = [
  ["Full Name", PROFILE.full_name],
  ["Student ID", PROFILE.student_id],
  ["Class", PROFILE.class_name],
  ["Faculty", PROFILE.faculty],
  ["Phone Number", PROFILE.phone],
  ["Email Address", PROFILE.email],
];

export default function Profile() {
  const [avatarOk, setAvatarOk] = useState(true);
  const initial = PROFILE.full_name.split(" ").pop().charAt(0);

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
              alt={PROFILE.full_name}
              onError={() => setAvatarOk(false)}
            />
          ) : (
            <div className="avatar">{initial}</div>
          )}
          <div>
            <div className="profile-name">{PROFILE.full_name}</div>
            <span className="role">Student / Developer</span>
          </div>
        </div>

        <div className="profile-grid">
          {FIELDS.map(([label, value]) => (
            <div className="field" key={label}>
              <label>{label}</label>
              <input value={value} readOnly />
            </div>
          ))}
        </div>
      </section>

      <h2 className="section-title">Project Resources</h2>
      <section className="resource-grid">
        {RESOURCES.map(({ title, desc, label, icon: Icon, href, download }) => (
          <div className="card resource" key={title}>
            <div className="resource-head">
              <div className="resource-icon"><Icon size={18} /></div>
              <strong>{title}</strong>
            </div>
            <p>{desc}</p>
            <a
              className="btn-primary"
              href={href}
              download={download || undefined}
              target={download ? undefined : "_blank"}
              rel="noreferrer"
            >
              {label}
            </a>
          </div>
        ))}
      </section>
    </>
  );
}