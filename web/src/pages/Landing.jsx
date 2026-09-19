import { useState } from "react";
import { Link } from "react-router-dom";
import AuthModal from "../components/AuthModal";
import {
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  FileSearch,
  ShieldCheck,
  Sparkles,
  Target,
  Brain,
  BarChart3,
  BriefcaseBusiness,
} from "lucide-react";

const faqs = [
  {
    question: "What is an ATS?",
    answer:
      "An Applicant Tracking System is software companies use to collect, organize, filter, and rank job applications before recruiters review them.",
  },
  {
    question: "How does SmartHire score my resume?",
    answer:
      "SmartHire analyzes resume structure, formatting, skills, keywords, content quality, and job-description relevance to produce an ATS-oriented score.",
  },
  {
    question: "Can I analyze my resume without a job description?",
    answer:
      "Yes. You can run a general resume analysis without providing a job description. Adding a job description enables keyword and job-match analysis.",
  },
  {
    question: "Does SmartHire support different industries?",
    answer:
      "Yes. The analysis is designed to work across technology, finance, healthcare, marketing, legal, operations, education, and other professional roles.",
  },
  {
    question: "Is my resume stored?",
    answer:
      "Your application architecture can store analysis history for your account, while the resume-processing flow is designed to minimize unnecessary exposure of the original document.",
  },
  {
    question: "Is SmartHire free?",
    answer:
      "SmartHire is designed around accessible resume analysis without forcing users into premium tiers just to understand their resume.",
  },
];

export default function Landing() {
  const [openFaq, setOpenFaq] = useState(null);
  const [authModal, setAuthModal] = useState(null);

  return (
    <div className="landing-page">
      {/* =====================================================
          NAVBAR
          ===================================================== */}

      <header className="mx-auto max-w-7xl px-4 py-3 landing-navbar">
        <div className="landing-container landing-nav-inner">
          <div className="landing-brand-section">
            <Link to="/" className="landing-brand">
              <span className="landing-brand-mark">
                <Sparkles size={17} />
              </span>

              <span>
                Smart<span>Hire</span>
              </span>
            </Link>

            {/* GitHub Star Button */}
            <a
              href="https://github.com/KalyanSai956/SmartHire_ATS"
              target="_blank"
              rel="noopener noreferrer"
              className="github-star-btn"
            >
              <svg
                className="github-icon"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  fill="currentColor"
                  d="M12 .5C5.65.5.5 5.65.5 12c0 5.09 3.29 9.4 7.86 10.92.57.1.78-.25.78-.55v-2.13c-3.2.7-3.87-1.54-3.87-1.54-.52-1.33-1.28-1.68-1.28-1.68-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.68 1.25 3.33.96.1-.74.4-1.25.73-1.54-2.55-.29-5.23-1.28-5.23-5.7 0-1.26.45-2.29 1.18-3.1-.12-.29-.51-1.47.11-3.06 0 0 .96-.31 3.15 1.18A10.9 10.9 0 0 1 12 6.58c.97 0 1.95.13 2.86.39 2.19-1.49 3.15-1.18 3.15-1.18.62 1.59.23 2.77.11 3.06.73.81 1.18 1.84 1.18 3.1 0 4.43-2.69 5.4-5.25 5.69.41.36.78 1.07.78 2.16v3.2c0 .31.21.66.79.55A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z"
                />
              </svg>

              <span>Star the repo</span>

              <span className="star-icon">★</span>
            </a>
          </div>

          <div className="landing-nav-actions">
            <button
              type="button"
              className="landing-login-link landing-auth-button"
              onClick={() => setAuthModal("login")}
            >
              Login
            </button>

            <button
              type="button"
              className="landing-nav-button landing-auth-button"
              onClick={() => setAuthModal("signup")}
            >
              Get started
              <ArrowRight size={15} />
            </button>
          </div>
        </div>
      </header>

      {/* =====================================================
          HERO
          ===================================================== */}

      <main>
        <section className="mx-auto max-w-5xl px-4 py-3 landing-hero">
          <div className="landing-container">
            <div className="landing-hero-content">
              <h1>
                Make every line
                <span> Count.</span>
              </h1>

              <div className="landing-hero-actions">
                <button
                  type="button"
                  className="landing-primary-button landing-auth-button"
                  onClick={() => setAuthModal("signup")}
                >
                  Analyze my resume
                  <ArrowRight size={17} />
                </button>

                <button
                  type="button"
                  className="landing-secondary-button landing-auth-button"
                  onClick={() => setAuthModal("login")}
                >
                  Login
                  <ArrowRight size={17} />
                </button>
              </div>
            </div>

            {/* HERO ANALYSIS PREVIEW */}

            <div className="landing-preview">
              <div className="preview-window">
                <div className="preview-topbar">
                  <div className="preview-dots">
                    <span />
                    <span />
                    <span />
                  </div>

                  <span>SmartHire Analysis</span>

                  <div />
                </div>

                <div className="preview-body">
                  <div className="preview-header">
                    <div>
                      <small>RESUME ANALYSIS</small>
                      <strong>Software Engineer</strong>
                    </div>

                    <span className="preview-status">ANALYZED</span>
                  </div>

                  <div className="preview-score-row">
                    <div className="preview-score">
                      <strong>81</strong>
                      <span>/ 100</span>
                    </div>

                    <div className="preview-score-copy">
                      <strong>Strong ATS compatibility</strong>
                      <p>
                        Your resume is performing well, with opportunities to
                        improve keyword coverage.
                      </p>
                    </div>
                  </div>

                  <div className="preview-bars">
                    <PreviewBar label="Formatting" value={90} />

                    <PreviewBar label="Content Quality" value={78} />

                    <PreviewBar label="ATS Compatibility" value={95} />

                    <PreviewBar label="Keywords & Skills" value={72} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
        {/* =====================================================
            FAQ
            ===================================================== */}

        <section
          id="faq"
          className="mx-auto max-w-5xl px-4 py-3 landing-section landing-faq"
        >
          <div className="landing-container landing-faq-container">
            <div className="landing-section-heading">
              <span className="landing-section-kicker">FAQ</span>
            </div>

            <div className="landing-faq-list">
              {faqs.map((faq, index) => {
                const isOpen = openFaq === index;

                return (
                  <div
                    className={`landing-faq-item ${isOpen ? "open" : ""}`}
                    key={faq.question}
                  >
                    <button
                      type="button"
                      onClick={() => setOpenFaq(isOpen ? null : index)}
                    >
                      <span>{faq.question}</span>

                      <ChevronDown size={18} className="landing-faq-icon" />
                    </button>

                    {isOpen && (
                      <div className="landing-faq-answer">
                        <p>{faq.answer}</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </section>
      </main>

      {/* =====================================================
          FOOTER
          ===================================================== */}

      <footer className="mx-auto max-w-5xl px-4 py-3 landing-footer">
        <div className="landing-container landing-footer-inner">
          <div className="landing-footer-brand">
            <Link to="/" className="landing-brand">
              <span className="landing-brand-mark">
                <Sparkles size={16} />
              </span>

              <span>SmartHire</span>
            </Link>

            <p>AI-powered resume analysis for smarter job applications.</p>
          </div>

          <div className="landing-footer-links">
            <div>
              <strong>Account</strong>

              <button type="button" onClick={() => setAuthModal("login")}>
                Login
              </button>

              <button type="button" onClick={() => setAuthModal("signup")}>
                Sign up
              </button>
            </div>

            <div>
              <strong>Support</strong>

              <a href="#faq">FAQ</a>
            </div>
          </div>
        </div>

        <div className="landing-footer-bottom">
          <div className="landing-container">
            <span>© {new Date().getFullYear()} SmartHire</span>

            <span>Built for smarter applications.</span>
          </div>
        </div>
      </footer>
      {authModal && (
        <AuthModal
          mode={authModal}
          onClose={() => setAuthModal(null)}
          onModeChange={(mode) => setAuthModal(mode)}
        />
      )}
    </div>
  );
}

/* =========================================================
   SMALL COMPONENTS
   ========================================================= */

function PreviewBar({ label, value }) {
  return (
    <div className="preview-bar">
      <div className="preview-bar-label">
        <span>{label}</span>
        <strong>{value}%</strong>
      </div>

      <div className="preview-bar-track">
        <span style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function Step({ number, title, description }) {
  return (
    <article className="landing-step">
      <span className="landing-step-number">{number}</span>

      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </article>
  );
}
