import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Check,
  FileText,
  Plus,
  Sparkles,
  Upload,
  X,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";
import {
  completeOnboarding,
  updateProfile,
  uploadProfileResume,
} from "../services/api";

const EXPERIENCE_OPTIONS = [
  "Student",
  "Fresher",
  "Less than 1 year",
  "1–2 years",
  "2–5 years",
  "5+ years",
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { accessToken, user } = useAuth();

  const [step, setStep] = useState(1);

  const [username, setUsername] = useState(
    user?.user_metadata?.full_name || user?.email?.split("@")[0] || "",
  );

  const [skills, setSkills] = useState([]);
  const [skillInput, setSkillInput] = useState("");

  const [targetRoles, setTargetRoles] = useState([]);
  const [roleInput, setRoleInput] = useState("");

  const [experience, setExperience] = useState("");

  const [resume, setResume] = useState(null);

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function addSkill() {
    const value = skillInput.trim();

    if (!value) return;

    const exists = skills.some(
      (skill) => skill.toLowerCase() === value.toLowerCase(),
    );

    if (!exists) {
      setSkills((current) => [...current, value]);
    }

    setSkillInput("");
  }

  function removeSkill(skill) {
    setSkills((current) => current.filter((item) => item !== skill));
  }

  function addRole() {
    const value = roleInput.trim();

    if (!value) return;

    const exists = targetRoles.some(
      (role) => role.toLowerCase() === value.toLowerCase(),
    );

    if (!exists) {
      setTargetRoles((current) => [...current, value]);
    }

    setRoleInput("");
  }

  function removeRole(role) {
    setTargetRoles((current) => current.filter((item) => item !== role));
  }

  function handleSkillKeyDown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      addSkill();
    }
  }

  function handleRoleKeyDown(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      addRole();
    }
  }

  function validateStep() {
    setError("");

    if (step === 1) {
      if (!username.trim()) {
        setError("Please enter a username.");
        return false;
      }

      if (username.trim().length < 2) {
        setError("Username must contain at least 2 characters.");
        return false;
      }
    }

    if (step === 2) {
      if (!skills.length) {
        setError("Add at least one skill.");
        return false;
      }
    }

    if (step === 3) {
      if (!targetRoles.length) {
        setError("Add at least one target role.");
        return false;
      }
    }

    if (step === 4) {
      if (!experience) {
        setError("Please select your experience level.");
        return false;
      }
    }

    if (step === 5) {
      if (!resume) {
        setError("Please upload your resume.");
        return false;
      }
    }

    return true;
  }

  async function nextStep() {
    if (!validateStep()) return;

    setBusy(true);
    setError("");

    try {
      if (step === 4) {
        await updateProfile({
          username: username.trim(),
          skills,
          targetRoles,
          experience,
          token: accessToken,
        });
      }

      if (step === 5) {
        await uploadProfileResume({
          file: resume,
          token: accessToken,
        });

        await completeOnboarding(accessToken);

        sessionStorage.setItem("smarthire_onboarding_completed", "true");

        navigate("/dashboard", {
          replace: true,
        });
        return;
      }

      setStep((current) => current + 1);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  function previousStep() {
    setError("");
    setStep((current) => Math.max(1, current - 1));
  }

  function handleResumeChange(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    const validTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];

    const validExtension = /\.(pdf|docx)$/i.test(file.name);

    if (!validExtension || !validTypes.includes(file.type)) {
      setError("Please upload a PDF or DOCX file.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("Resume must be smaller than 5 MB.");
      return;
    }

    setError("");
    setResume(file);
  }

  const progress = `${(step / 5) * 100}%`;

  return (
    <div className="mx-auto max-w-5xl px-6 py-5 onboarding-page">
      <div className="onboarding-top">
        <div className="brand">
          <span className="brand-mark">
            <Sparkles size={17} />
          </span>

          <span>
            Smart<span>Hire</span>
          </span>
        </div>

        <span className="onboarding-step">Step {step} of 5</span>
      </div>

      <main className="onboarding-content">
        <div className="onboarding-header">
          <p className="eyebrow">BUILD YOUR CAREER PROFILE</p>
        </div>

        <section className="onboarding-card">
          {step === 1 && (
            <div className="onboarding-section">
              <h2>What should we call you?</h2>

              <p>
                Choose the name you'd like SmartHire to use throughout your
                career workspace.
              </p>

              <label className="auth-field">
                <span>Username</span>

                <div>
                  <input
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    placeholder="e.g. Tony Stark"
                    autoFocus
                  />
                </div>
              </label>
            </div>
          )}

          {step === 2 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <Plus size={22} />
              </span>

              <h2>What skills do you have?</h2>

              <p>
                Add your current technical and professional skills. You can add
                as many as you want.
              </p>

              <div className="tag-input">
                <input
                  value={skillInput}
                  onChange={(event) => setSkillInput(event.target.value)}
                  onKeyDown={handleSkillKeyDown}
                  placeholder="Python, React, FastAPI..."
                  autoFocus
                />

                <button
                  type="button"
                  className="button secondary"
                  onClick={addSkill}
                >
                  <Plus size={16} />
                  Add
                </button>
              </div>

              <div className="onboarding-tags">
                {skills.map((skill) => (
                  <span className="onboarding-tag" key={skill}>
                    {skill}

                    <button type="button" onClick={() => removeSkill(skill)}>
                      <X size={13} />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <ArrowRight size={22} />
              </span>

              <h2>What roles are you targeting?</h2>

              <p>Tell SmartHire which roles you're interested in.</p>

              <div className="tag-input">
                <input
                  value={roleInput}
                  onChange={(event) => setRoleInput(event.target.value)}
                  onKeyDown={handleRoleKeyDown}
                  placeholder="AI Engineer, Software Engineer..."
                  autoFocus
                />

                <button
                  type="button"
                  className="button secondary"
                  onClick={addRole}
                >
                  <Plus size={16} />
                  Add
                </button>
              </div>

              <div className="onboarding-tags">
                {targetRoles.map((role) => (
                  <span className="onboarding-tag" key={role}>
                    {role}

                    <button type="button" onClick={() => removeRole(role)}>
                      <X size={13} />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <Check size={22} />
              </span>

              <h2>What's your experience level?</h2>

              <p>
                This helps SmartHire understand which opportunities and
                interview difficulty are appropriate for you.
              </p>

              <div className="experience-options">
                {EXPERIENCE_OPTIONS.map((option) => (
                  <button
                    type="button"
                    key={option}
                    className={
                      experience === option
                        ? "experience-option selected"
                        : "experience-option"
                    }
                    onClick={() => setExperience(option)}
                  >
                    <span>{option}</span>

                    {experience === option && <Check size={17} />}
                  </button>
                ))}
              </div>
            </div>
          )}

          {step === 5 && (
            <div className="onboarding-section">
              <span className="onboarding-icon">
                <FileText size={22} />
              </span>

              <h2>Upload your resume</h2>

              <p>
                SmartHire will analyze your resume and use it as the foundation
                for your career workspace.
              </p>

              <label className="resume-upload-box">
                <input
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleResumeChange}
                  hidden
                />

                {resume ? (
                  <>
                    <FileText size={28} />

                    <strong>{resume.name}</strong>

                    <span>{(resume.size / 1024 / 1024).toFixed(2)} MB</span>
                  </>
                ) : (
                  <>
                    <Upload size={28} />

                    <strong>Choose your resume</strong>

                    <span>PDF or DOCX · Maximum 5 MB</span>
                  </>
                )}
              </label>
            </div>
          )}

          {error && <div className="auth-error onboarding-error">{error}</div>}

          <div className="onboarding-actions">
            {step > 1 ? (
              <button
                type="button"
                className="button secondary"
                onClick={previousStep}
                disabled={busy}
              >
                Back
              </button>
            ) : (
              <span />
            )}

            <button
              type="button"
              className="button primary"
              onClick={nextStep}
              disabled={busy}
            >
              {busy
                ? "Saving..."
                : step === 5
                  ? "Complete Profile"
                  : "Continue"}

              <ArrowRight size={16} />
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
