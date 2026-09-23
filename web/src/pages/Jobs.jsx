import {
  BriefcaseBusiness,
  Sparkles,
  ArrowLeft,
  Bell,
  Target,
  Brain,
} from "lucide-react";
import { Link } from "react-router-dom";

import "../CSS/Jobs.css";

export default function Job() {
  return (
    <div className="job-coming-page">
      <div className="job-coming-card">
        {/* ICON */}

        <h1>
          Coming
          <span> Soon...</span>
        </h1>

        <p className="job-coming-description">
          SmartHire is building a smarter way to discover opportunities that
          actually match your skills, experience, career goals, and readiness.
        </p>
        {/* FOOTER */}

        <div className="job-coming-footer">
          <Link to="/dashboard" className="job-back-button">
            <ArrowLeft size={15} />
            Back to Dashboard
          </Link>

          <span className="job-coming-note">We're working on it.</span>
        </div>
      </div>
    </div>
  );
}
