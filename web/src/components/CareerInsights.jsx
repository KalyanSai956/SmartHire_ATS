import { NavLink } from "react-router-dom";

export default function CareerInsights() {
  return (
    <aside className="career-insights">
      {/* =====================================================
          NAVIGATION
          ===================================================== */}

      <div className="career-insights-header">
        <span className="career-insights-label">SMART HIRE</span>
      </div>

      <nav className="career-insights-nav">
        <NavLink
          to="/history"
          className={({ isActive }) =>
            `career-insight-link ${isActive ? "active" : ""}`
          }
        >
          <div>
            <strong>ATS Scores</strong>
          </div>
        </NavLink>

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `career-insight-link ${isActive ? "active" : ""}`
          }
        >
          <div>
            <strong>AI Settings</strong>
          </div>
        </NavLink>
      </nav>

      {/* =====================================================
          CAREER SIGNAL
          ===================================================== */}

      <div className="career-insights-divider" />

      <div className="career-signal-header">
        <span>CAREER SIGNAL</span>
      </div>

      <div className="insight-card">
        <div>
          <span>RESUME INTELLIGENCE</span>
          <strong>Keep improving</strong>
        </div>
      </div>

      <div className="insight-card">
        <div>
          <span>REAL TIME JOB AGENT</span>
          <strong>Build your baseline</strong>
        </div>
      </div>
    </aside>
  );
}
