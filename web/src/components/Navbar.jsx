import { Link, NavLink, useNavigate } from "react-router-dom";
import { LogOut, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const name =
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "User";

  const links = [
    ["Dashboard", "/dashboard"],
    ["Resume ATS", "/analyze"],
    ["Interview", "/interview/setup"],
    ["Review", "/history"],
    ["Interview History", "/interviews/history"],
  ];

  async function logout() {
    try {
      await signOut();
      navigate("/", { replace: true });
    } catch (error) {
      console.error("Logout failed:", error);
    }
  }

  return (
    <header className="topbar">
      <div className="topbar-inner">
        {/* LEFT — LOGO */}
        <Link to="/dashboard" className="brand">
          <span className="brand-mark">
            <Sparkles size={15} strokeWidth={2.5} />
          </span>

          <span className="brand-text">
            Smart<span>Hire</span>
          </span>
        </Link>

        {/* CENTER — NAVIGATION */}
        <nav className="desktop-nav">
          {links.map(([label, to]) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `nav-link ${isActive ? "active" : ""}`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* RIGHT — USER + SIGN OUT */}
        <div className="topbar-actions">
          <span className="user-name">{name}</span>

          <button type="button" className="signout-button" onClick={logout}>
            <LogOut size={15} />
            <span>Sign out</span>
          </button>
        </div>
      </div>
    </header>
  );
}
