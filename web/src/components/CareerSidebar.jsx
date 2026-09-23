import { useEffect, useState } from "react";

import { getProfile } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function CareerSidebar() {
  const { accessToken } = useAuth();

  const [profile, setProfile] = useState(null);

  useEffect(() => {
    if (!accessToken) return;

    let active = true;

    async function loadProfile() {
      try {
        const data = await getProfile(accessToken);

        if (active) {
          setProfile(data);
        }
      } catch {
        // Sidebar should never break the main application.
      }
    }

    loadProfile();

    return () => {
      active = false;
    };
  }, [accessToken]);

  const targetRole = profile?.target_roles?.length
    ? profile.target_roles[0]
    : "Target role not set";

  const skills = Array.isArray(profile?.skills) ? profile.skills : [];

  return (
    <aside className="career-sidebar">
      {/* =====================================================
          HEADER
          ===================================================== */}

      <div className="career-sidebar-header">
        <span className="career-sidebar-label">CAREER PROFILE</span>
      </div>

      {/* =====================================================
          TARGET ROLE
          ===================================================== */}

      <div className="career-target-card">
        <span>TARGET ROLE</span>

        <strong>{targetRole}</strong>
      </div>

      {/* =====================================================
          SKILLS
          ===================================================== */}

      <div className="career-sidebar-section">
        <div className="career-sidebar-title">Skills</div>

        {skills.length > 0 ? (
          <div className="career-sidebar-skills">
            {skills.slice(0, 8).map((skill, index) => (
              <span key={`${skill}-${index}`}>{skill}</span>
            ))}
          </div>
        ) : (
          <p className="career-sidebar-muted">
            Add your skills to build your career profile.
          </p>
        )}
      </div>

      {/* =====================================================
          PROFILE INFORMATION
          ===================================================== */}

      <div className="career-sidebar-divider" />

      <div className="career-sidebar-info">
        <div className="career-sidebar-info-item">
          <span>Experience</span>

          <strong>{profile?.experience || "Not specified"}</strong>
        </div>

        <div className="career-sidebar-info-item">
          <span>Graduation</span>

          <strong>{profile?.graduation_year || "Not specified"}</strong>
        </div>

        <div className="career-sidebar-info-item">
          <span>Resume</span>

          <strong>
            {profile?.resume_filename ? "Connected" : "Not connected"}
          </strong>
        </div>
      </div>

      {/* =====================================================
          PROFILE STATUS
          ===================================================== */}
    </aside>
  );
}
