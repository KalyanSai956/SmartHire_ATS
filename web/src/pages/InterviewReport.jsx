import {
  ArrowLeft,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  Clock3,
  Sparkles,
  Target,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getInterviewReport } from "../services/api";

function ScoreRing({ label, score, large = false }) {
  const value = Number(score) || 0;

  return (
    <div
      className={
        large
          ? "interview-score-ring interview-score-ring-large"
          : "interview-score-ring"
      }
    >
      <div
        className="interview-score-ring-inner"
        style={{
          "--score": `${value * 3.6}deg`,
        }}
      >
        <strong>{value}</strong>
        <span>/100</span>
      </div>

      <label>{label}</label>
    </div>
  );
}

function ScoreBar({ label, value }) {
  const score = Number(value) || 0;

  return (
    <div className="report-score-row">
      <div className="report-score-row-header">
        <span>{label}</span>
        <strong>{score}/100</strong>
      </div>

      <div className="report-score-track">
        <div
          className="report-score-fill"
          style={{
            width: `${Math.min(100, Math.max(0, score))}%`,
          }}
        />
      </div>
    </div>
  );
}

export default function InterviewReport() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const { session: authSession } = useAuth();

  const token = authSession?.access_token;

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [expandedQuestion, setExpandedQuestion] = useState(null);

  const loadReport = useCallback(async () => {
    if (!token || !sessionId) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const data = await getInterviewReport({
        sessionId,
        token,
      });

      setReport(data);
    } catch (err) {
      console.error("Failed to load interview report:", err);

      setError(err?.message || "Unable to load interview report.");
    } finally {
      setLoading(false);
    }
  }, [token, sessionId]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  if (loading) {
    return (
      <div className="interview-report-page">
        <div className="interview-report-loading">
          <div className="report-loading-orb">SH</div>

          <h2>Preparing your interview report</h2>

          <p>Aggregating your answers, evaluations and performance.</p>

          <div className="report-loading-line" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-5 interview-report-page">
        <div className="report-error-card">
          <CircleAlert size={28} />

          <h2>Report could not be loaded</h2>

          <p>{error}</p>

          <div className="report-action-row">
            <button
              type="button"
              className="report-secondary-button"
              onClick={loadReport}
            >
              Try again
            </button>

            <button
              type="button"
              className="report-primary-button"
              onClick={() => navigate("/interviews/history")}
            >
              Interview history
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!report) {
    return null;
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-5 interview-report-page">
      <main className="interview-report-container">
        {/* HEADER */}

        <div className="report-page-header">
          <button
            type="button"
            className="report-back-button"
            onClick={() => navigate("/interviews/history")}
          >
            <ArrowLeft size={17} />
            Interview history
          </button>

          <span className="report-header-kicker">INTERVIEW REPORT</span>

          <h2>{report.role || "Interview"}</h2>

          <p>
            {report.interview_type || "Mixed"} interview
            <span> · </span>
            {report.difficulty || "Medium"} difficulty
          </p>
        </div>

        {/* SCORE HERO */}

        <section className="report-score-hero">
          <div className="report-score-hero-main">
            <div>
              <span className="report-kicker">OVERALL PERFORMANCE</span>

              <h2>Interview performance</h2>

              <p>
                Your score is calculated from the evaluations recorded during
                this interview.
              </p>
            </div>

            <ScoreRing label="Overall" score={report.overall_score} large />
          </div>

          <div className="report-metric-grid">
            <div className="report-metric-card">
              <Target size={18} />
              <span>Technical</span>
              <strong>{report.technical_score}/100</strong>
            </div>

            <div className="report-metric-card">
              <Sparkles size={18} />
              <span>Communication</span>
              <strong>{report.communication_score}/100</strong>
            </div>

            <div className="report-metric-card">
              <CheckCircle2 size={18} />
              <span>Problem solving</span>
              <strong>{report.problem_solving_score}/100</strong>
            </div>

            <div className="report-metric-card">
              <Clock3 size={18} />
              <span>Evaluated</span>
              <strong>
                {report.evaluated_questions}/{report.total_questions}
              </strong>
            </div>
          </div>
        </section>

        {/* SUMMARY */}

        <section className="report-panel">
          <div className="report-panel-heading">
            <div>
              <span className="report-kicker">SUMMARY</span>

              <h2>What your interview showed</h2>
            </div>
          </div>

          <p className="report-summary">
            {report.summary || "No summary was generated for this interview."}
          </p>
        </section>

        {/* SCORE BREAKDOWN */}

        <section className="report-panel">
          <div className="report-panel-heading">
            <div>
              <span className="report-kicker">PERFORMANCE</span>

              <h2>Score breakdown</h2>
            </div>
          </div>

          <div className="report-score-bars">
            <ScoreBar
              label="Technical knowledge"
              value={report.technical_score}
            />

            <ScoreBar
              label="Communication"
              value={report.communication_score}
            />

            <ScoreBar
              label="Problem solving"
              value={report.problem_solving_score}
            />

            <ScoreBar label="Overall" value={report.overall_score} />
          </div>
        </section>

        {/* STRENGTHS + WEAKNESSES */}

        <div className="report-two-column">
          <section className="report-panel">
            <div className="report-panel-heading">
              <CheckCircle2 size={19} />

              <div>
                <span className="report-kicker">STRENGTHS</span>

                <h2>What went well</h2>
              </div>
            </div>

            <div className="report-list">
              {report.strengths?.length ? (
                report.strengths.map((item, index) => (
                  <div
                    className="report-list-item report-strength"
                    key={`${item}-${index}`}
                  >
                    <CheckCircle2 size={17} />
                    <span>{item}</span>
                  </div>
                ))
              ) : (
                <p className="report-empty">No explicit strengths recorded.</p>
              )}
            </div>
          </section>

          <section className="report-panel">
            <div className="report-panel-heading">
              <CircleAlert size={19} />

              <div>
                <span className="report-kicker">AREAS TO IMPROVE</span>

                <h2>Focus next</h2>
              </div>
            </div>

            <div className="report-list">
              {report.weaknesses?.length ? (
                report.weaknesses.map((item, index) => (
                  <div
                    className="report-list-item report-weakness"
                    key={`${item}-${index}`}
                  >
                    <CircleAlert size={17} />
                    <span>{item}</span>
                  </div>
                ))
              ) : (
                <p className="report-empty">No major weaknesses recorded.</p>
              )}
            </div>
          </section>
        </div>

        {/* RECOMMENDED TOPICS */}

        <section className="report-panel">
          <div className="report-panel-heading">
            <Sparkles size={19} />

            <div>
              <span className="report-kicker">RECOMMENDED TOPICS</span>

              <h2>Prepare before your next interview</h2>
            </div>
          </div>

          {report.recommended_topics?.length ? (
            <div className="report-topic-grid">
              {report.recommended_topics.map((topic, index) => (
                <div className="report-topic" key={`${topic}-${index}`}>
                  <span>{String(index + 1).padStart(2, "0")}</span>

                  <strong>{topic}</strong>
                </div>
              ))}
            </div>
          ) : (
            <p className="report-empty">No specific topics were generated.</p>
          )}
        </section>

        {/* QUESTION BREAKDOWN */}

        <section className="report-panel">
          <div className="report-panel-heading">
            <div>
              <span className="report-kicker">QUESTION REVIEW</span>

              <h2>Interview breakdown</h2>
            </div>

            <span className="report-count">
              {report.evaluated_questions}/{report.total_questions} evaluated
            </span>
          </div>

          <div className="report-question-list">
            {report.questions?.map((item, index) => {
              const isExpanded = expandedQuestion === index;

              const score = item.evaluation?.overall_score;

              return (
                <div
                  className="report-question"
                  key={item.question_id || `${index}`}
                >
                  <button
                    type="button"
                    className="report-question-header"
                    onClick={() =>
                      setExpandedQuestion(isExpanded ? null : index)
                    }
                  >
                    <div className="report-question-number">
                      Q
                      {String(item.question_order || index + 1).padStart(
                        2,
                        "0",
                      )}
                    </div>

                    <div className="report-question-title">
                      <strong>{item.question}</strong>

                      <span>
                        {item.category}
                        {item.skill ? ` · ${item.skill}` : ""}
                      </span>
                    </div>

                    <div className="report-question-score">
                      {score != null ? `${score}/100` : "Not evaluated"}
                    </div>

                    {isExpanded ? (
                      <ChevronUp size={18} />
                    ) : (
                      <ChevronDown size={18} />
                    )}
                  </button>

                  {isExpanded && (
                    <div className="report-question-body">
                      {item.answer?.answer_text && (
                        <div className="report-answer-block">
                          <span>YOUR ANSWER</span>

                          <p>{item.answer.answer_text}</p>
                        </div>
                      )}

                      {item.evaluation && (
                        <div className="report-evaluation-block">
                          <div className="report-mini-scores">
                            <span>
                              Technical {item.evaluation.technical_score}
                            </span>

                            <span>
                              Relevance {item.evaluation.relevance_score}
                            </span>

                            <span>Clarity {item.evaluation.clarity_score}</span>

                            <span>Depth {item.evaluation.depth_score}</span>
                          </div>

                          <p>{item.evaluation.feedback}</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        <div className="report-bottom-actions">
          <button
            type="button"
            className="report-secondary-button"
            onClick={() => navigate("/interviews/history")}
          >
            View interview history
          </button>

          <button
            type="button"
            className="report-primary-button"
            onClick={() => navigate("/interview/setup")}
          >
            Practice another interview
          </button>
        </div>
      </main>
    </div>
  );
}
