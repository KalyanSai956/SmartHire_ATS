import { AlertCircle, CheckCircle2 } from "lucide-react";

function getSkillName(skill, index) {
  if (typeof skill === "string") {
    return skill.trim();
  }

  if (!skill || typeof skill !== "object") {
    return `Skill ${index + 1}`;
  }

  return skill.name || skill.skill || skill.title || `Skill ${index + 1}`;
}

export default function SkillValidation({
  totalSkills = 0,
  validatedSkills = 0,
  validationRate = 0,
  matchedSkills = [],
  missingSkills = [],
}) {
  return (
    <section className="skill-validation-card">
      {/* HEADER */}
      <div className="skill-validation-header">
        <div>
          <span className="skill-validation-kicker">SKILL VALIDATION</span>

          <h2>Skills Detected in Your Resume</h2>

          <p>
            Skills are validated when they are supported by project or
            experience evidence.
          </p>
        </div>
      </div>

      {/* STATISTICS */}
      <div className="skill-validation-stats">
        <div className="skill-stat">
          <span className="skill-stat-label">Total Skills</span>
          <strong>{totalSkills}</strong>
        </div>

        <div className="skill-stat">
          <span className="skill-stat-label">Validated</span>
          <strong className="validated-number">{validatedSkills}</strong>
        </div>

        <div className="skill-stat">
          <span className="skill-stat-label">Validation Rate</span>
          <strong
            className={
              validationRate >= 70
                ? "rate-good"
                : validationRate >= 40
                  ? "rate-warning"
                  : "rate-low"
            }
          >
            {Math.round(validationRate)}%
          </strong>
        </div>
      </div>

      {/* VALIDATED SKILLS */}
      <div className="skill-validation-section">
        <div className="skill-section-heading">
          <h3>Validated Skills</h3>
          <span className="skill-count success-count">
            {matchedSkills.length}
          </span>
        </div>

        {matchedSkills.length > 0 ? (
          <div className="skill-chip-list">
            {matchedSkills.map((skill, index) => {
              const name = getSkillName(skill, index);

              return (
                <span
                  className="skill-chip skill-chip-success"
                  key={`${name}-${index}`}
                >
                  <CheckCircle2 size={13} strokeWidth={2.2} />
                  <span>{name}</span>
                </span>
              );
            })}
          </div>
        ) : (
          <div className="skill-empty">No validated skills found.</div>
        )}
      </div>

      {/* UNVALIDATED SKILLS */}
      <div className="skill-validation-section unvalidated-section">
        <div className="skill-section-heading">
          <h3>Unvalidated Skills</h3>

          <span className="skill-count danger-count">
            {missingSkills.length}
          </span>
        </div>

        <p className="skill-section-description">
          These skills are listed but are not tied to a project or experience
          bullet.
        </p>

        {missingSkills.length > 0 ? (
          <div className="skill-chip-list">
            {missingSkills.map((skill, index) => {
              const name = getSkillName(skill, index);

              return (
                <span
                  className="skill-chip skill-chip-danger"
                  key={`${name}-${index}`}
                >
                  <AlertCircle size={13} strokeWidth={2.2} />
                  <span>{name}</span>
                </span>
              );
            })}
          </div>
        ) : (
          <div className="skill-empty skill-empty-success">
            All detected skills have supporting evidence.
          </div>
        )}
      </div>
    </section>
  );
}
