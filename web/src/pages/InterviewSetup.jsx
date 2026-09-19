import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createInterviewSession, getProfile } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "../styles.css";

const INTERVIEW_TYPES = [
  { value: "mixed", label: "Mixed", description: "Technical + behavioral" },
  {
    value: "technical",
    label: "Technical",
    description: "Technical knowledge & problem solving",
  },
  {
    value: "behavioral",
    label: "Behavioral",
    description: "Experience & communication",
  },
];

const DIFFICULTIES = [
  {
    value: "easy",
    label: "Easy",
    description: "Fundamentals and basic concepts",
  },
  {
    value: "medium",
    label: "Medium",
    description: "Real interview-level questions",
  },
  { value: "hard", label: "Hard", description: "Deep technical challenges" },
];

export default function InterviewSetup() {
  const navigate = useNavigate();
  const { session } = useAuth();

  const [profile, setProfile] = useState(null);

  const [role, setRole] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [interviewType, setInterviewType] = useState("mixed");
  const [difficulty, setDifficulty] = useState("medium");

  const [questionCount, setQuestionCount] = useState(10);
  const [durationMinutes, setDurationMinutes] = useState(30);

  const [focusInput, setFocusInput] = useState("");
  const [focusAreas, setFocusAreas] = useState([]);

  const [includeCoding, setIncludeCoding] = useState(false);
  const [includeSystemDesign, setIncludeSystemDesign] = useState(false);

  const [loadingProfile, setLoadingProfile] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const token = session?.access_token;

  useEffect(() => {
    async function loadProfile() {
      if (!token) {
        setLoadingProfile(false);
        return;
      }

      try {
        const data = await getProfile(token);

        setProfile(data);

        if (data?.target_roles?.length > 0) {
          setRole(data.target_roles[0]);
        }
      } catch (err) {
        console.error("Failed to load career profile:", err);
      } finally {
        setLoadingProfile(false);
      }
    }

    loadProfile();
  }, [token]);

  const estimatedMinutes = useMemo(() => {
    return durationMinutes;
  }, [durationMinutes]);

  function addFocusArea() {
    const value = focusInput.trim();

    if (!value) {
      return;
    }

    if (value.length > 100) {
      setError("Each focus area must be 100 characters or less.");
      return;
    }

    if (focusAreas.length >= 10) {
      setError("You can specify a maximum of 10 focus areas.");
      return;
    }

    const exists = focusAreas.some(
      (item) => item.toLowerCase() === value.toLowerCase(),
    );

    if (exists) {
      setError("That focus area has already been added.");
      return;
    }

    setFocusAreas((current) => [...current, value]);
    setFocusInput("");
    setError("");
  }

  function removeFocusArea(value) {
    setFocusAreas((current) => current.filter((item) => item !== value));
  }

  function handleFocusKeyDown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      addFocusArea();
    }
  }

  function handleInterviewTypeChange(value) {
    setInterviewType(value);

    if (value === "behavioral") {
      setIncludeCoding(false);
      setIncludeSystemDesign(false);
    }

    setError("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!token) {
      navigate("/login");
      return;
    }

    const cleanedRole = role.trim();

    if (!cleanedRole) {
      setError("Please enter the role you want to practice for.");
      return;
    }

    if (cleanedRole.length < 2) {
      setError("Role must contain at least 2 characters.");
      return;
    }

    if (interviewType === "behavioral") {
      if (includeCoding || includeSystemDesign) {
        setError(
          "Coding and system design cannot be enabled for a behavioral interview.",
        );
        return;
      }
    }

    setSubmitting(true);
    setError("");

    try {
      const interview = await createInterviewSession({
        role: cleanedRole,
        jobDescription: jobDescription.trim(),
        interviewType,
        difficulty,
        configuration: {
          questionCount,
          durationMinutes,
          focusAreas,
          includeCoding,
          includeSystemDesign,
        },
        token,
      });

      if (!interview?.id) {
        throw new Error("Interview session was created without an ID.");
      }

      navigate(`/interview/${interview.id}`, {
        state: {
          interview,
        },
      });
    } catch (err) {
      console.error("Failed to create interview:", err);

      setError(
        err?.message || "Unable to create the interview. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loadingProfile) {
    return (
      <div className="interview-setup-page">
        <div className="interview-setup-shell">
          <div className="interview-setup-loading">
            Loading your career profile...
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-5 interview-setup-page">
      <div className="interview-setup-shell">
        <div className="interview-setup-header">
          <div>
            <span className="interview-eyebrow">INTERVIEW ARENA</span>
          </div>

          <button
            type="button"
            className="interview-back-button"
            onClick={() => navigate("/dashboard")}
          >
            ← Dashboard
          </button>
        </div>

        <form className="interview-setup-form" onSubmit={handleSubmit}>
          {/* ROLE */}
          <section className="interview-card">
            <div className="interview-card-heading">
              <div>
                <span className="interview-section-number">01</span>
                <h2>Target role</h2>
              </div>

              {profile?.target_roles?.length > 0 && (
                <span className="interview-profile-hint">
                  From your career profile
                </span>
              )}
            </div>

            <label htmlFor="interview-role">Role</label>

            <input
              id="interview-role"
              type="text"
              value={role}
              onChange={(event) => setRole(event.target.value)}
              placeholder="e.g. AI Engineer"
              maxLength={200}
              required
            />

            {profile?.target_roles?.length > 0 && (
              <div className="interview-suggestions">
                {profile.target_roles.slice(0, 5).map((targetRole) => (
                  <button
                    type="button"
                    key={targetRole}
                    onClick={() => setRole(targetRole)}
                  >
                    {targetRole}
                  </button>
                ))}
              </div>
            )}
          </section>

          {/* JOB DESCRIPTION */}
          <section className="interview-card">
            <div className="interview-card-heading">
              <div>
                <span className="interview-section-number">02</span>
                <h2>Job description</h2>
              </div>

              <span className="interview-optional">Optional</span>
            </div>

            <label htmlFor="interview-jd">Paste the job description</label>

            <textarea
              id="interview-jd"
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
              placeholder="Paste the job description here. The interview will use it to make questions more relevant to the position."
              maxLength={20000}
              rows={9}
            />

            <div className="interview-field-meta">
              <span>Recommended for role-specific interviews</span>

              <span>{jobDescription.length}/20,000</span>
            </div>
          </section>

          {/* TYPE + DIFFICULTY */}
          <section className="interview-card">
            <div className="interview-card-heading">
              <div>
                <span className="interview-section-number">03</span>
                <h2>Interview style</h2>
              </div>
            </div>

            <div className="interview-option-grid">
              <div>
                <label>Interview type</label>

                <div className="interview-option-list">
                  {INTERVIEW_TYPES.map((item) => (
                    <button
                      type="button"
                      key={item.value}
                      className={`interview-option ${
                        interviewType === item.value ? "selected" : ""
                      }`}
                      onClick={() => handleInterviewTypeChange(item.value)}
                    >
                      <span className="interview-option-title">
                        {item.label}
                      </span>

                      <span className="interview-option-description">
                        {item.description}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label>Difficulty</label>

                <div className="interview-option-list">
                  {DIFFICULTIES.map((item) => (
                    <button
                      type="button"
                      key={item.value}
                      className={`interview-option ${
                        difficulty === item.value ? "selected" : ""
                      }`}
                      onClick={() => {
                        setDifficulty(item.value);
                        setError("");
                      }}
                    >
                      <span className="interview-option-title">
                        {item.label}
                      </span>

                      <span className="interview-option-description">
                        {item.description}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* INTERVIEW SIZE */}
          <section className="interview-card">
            <div className="interview-card-heading">
              <div>
                <span className="interview-section-number">04</span>
                <h2>Interview size</h2>
              </div>
            </div>

            <div className="interview-slider-grid">
              <div className="interview-slider-block">
                <div className="interview-slider-label">
                  <label htmlFor="question-count">Questions</label>

                  <strong>{questionCount}</strong>
                </div>

                <input
                  id="question-count"
                  type="range"
                  min="5"
                  max="20"
                  step="1"
                  value={questionCount}
                  onChange={(event) =>
                    setQuestionCount(Number(event.target.value))
                  }
                />

                <div className="interview-range-meta">
                  <span>5</span>
                  <span>20</span>
                </div>
              </div>

              <div className="interview-slider-block">
                <div className="interview-slider-label">
                  <label htmlFor="duration">Duration</label>

                  <strong>{durationMinutes} min</strong>
                </div>

                <input
                  id="duration"
                  type="range"
                  min="10"
                  max="90"
                  step="5"
                  value={durationMinutes}
                  onChange={(event) =>
                    setDurationMinutes(Number(event.target.value))
                  }
                />

                <div className="interview-range-meta">
                  <span>10 min</span>
                  <span>90 min</span>
                </div>
              </div>
            </div>

            <div className="interview-duration-summary">
              <span>Estimated interview window</span>
              <strong>{estimatedMinutes} minutes</strong>
            </div>
          </section>

          {/* FOCUS AREAS */}
          <section className="interview-card">
            <div className="interview-card-heading">
              <div>
                <span className="interview-section-number">05</span>
                <h2>Focus areas</h2>
              </div>

              <span className="interview-optional">Optional</span>
            </div>

            <label htmlFor="focus-area">Skills or topics to emphasize</label>

            <div className="interview-focus-input">
              <input
                id="focus-area"
                type="text"
                value={focusInput}
                onChange={(event) => setFocusInput(event.target.value)}
                onKeyDown={handleFocusKeyDown}
                placeholder="e.g. Python, NLP, FastAPI"
                maxLength={100}
              />

              <button type="button" onClick={addFocusArea}>
                Add
              </button>
            </div>

            {focusAreas.length > 0 && (
              <div className="interview-focus-tags">
                {focusAreas.map((area) => (
                  <span className="interview-focus-tag" key={area}>
                    {area}

                    <button
                      type="button"
                      onClick={() => removeFocusArea(area)}
                      aria-label={`Remove ${area}`}
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}

            <p className="interview-help-text">
              Add up to 10 topics. These will influence question selection and
              evaluation later.
            </p>
          </section>

          {/* ADVANCED */}
          <section className="interview-card">
            <div className="interview-card-heading">
              <div>
                <span className="interview-section-number">06</span>
                <h2>Advanced topics</h2>
              </div>
            </div>

            <div className="interview-toggle-list">
              <label
                className={`interview-toggle ${
                  includeCoding ? "enabled" : ""
                } ${interviewType === "behavioral" ? "disabled" : ""}`}
              >
                <span>
                  <strong>Coding questions</strong>
                  <small>
                    Include programming and problem-solving questions.
                  </small>
                </span>

                <input
                  type="checkbox"
                  checked={includeCoding}
                  disabled={interviewType === "behavioral"}
                  onChange={(event) => setIncludeCoding(event.target.checked)}
                />

                <span className="interview-toggle-slider" />
              </label>

              <label
                className={`interview-toggle ${
                  includeSystemDesign ? "enabled" : ""
                } ${interviewType === "behavioral" ? "disabled" : ""}`}
              >
                <span>
                  <strong>System design</strong>
                  <small>
                    Include architecture and system design questions.
                  </small>
                </span>

                <input
                  type="checkbox"
                  checked={includeSystemDesign}
                  disabled={interviewType === "behavioral"}
                  onChange={(event) =>
                    setIncludeSystemDesign(event.target.checked)
                  }
                />

                <span className="interview-toggle-slider" />
              </label>
            </div>

            {interviewType === "behavioral" && (
              <p className="interview-help-text">
                Coding and system design are unavailable for behavioral
                interviews.
              </p>
            )}
          </section>

          {/* ERROR */}
          {error && <div className="interview-error">{error}</div>}

          {/* SUBMIT */}
          <div className="interview-setup-footer">
            <div>
              <span>Ready to practice?</span>
              <strong>
                {questionCount} questions · {durationMinutes} minutes
              </strong>
            </div>

            <button
              type="submit"
              className="interview-start-button"
              disabled={submitting}
            >
              {submitting ? "Creating interview..." : "Create interview →"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
