import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock3,
  FileText,
  LoaderCircle,
  Target,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getInterviewHistory } from "../services/api";

function formatDate(value) {
  if (!value) {
    return "Unknown date";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown date";
  }

  return date.toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function StatusBadge({ status }) {
  const normalized = String(status || "").toLowerCase();

  const label =
    normalized === "completed"
      ? "Completed"
      : normalized === "active"
        ? "In progress"
        : normalized === "paused"
          ? "Paused"
          : normalized === "abandoned"
            ? "Abandoned"
            : "Not started";

  return (
    <span className={`history-status history-status-${normalized}`}>
      {label}
    </span>
  );
}

export default function InterviewHistory() {
  const navigate = useNavigate();

  const { session: authSession } = useAuth();

  const token = authSession?.access_token;

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadHistory = useCallback(async () => {
    if (!token) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const data = await getInterviewHistory({
        token,
      });

      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Failed to load interview history:", err);

      setError(err?.message || "Unable to load interview history.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const completedItems = items.filter((item) => item.status === "completed");

  const scoredItems = completedItems.filter(
    (item) => item.overall_score != null,
  );

  const averageScore =
    scoredItems.length > 0
      ? Math.round(
          scoredItems.reduce(
            (sum, item) => sum + Number(item.overall_score || 0),
            0,
          ) / scoredItems.length,
        )
      : null;

  return (
    <div className="mx-auto max-w-5xl px-6 py-5 interview-report-page">
      <main className="interview-report-container">
        <div className="report-page-header">
          <button
            type="button"
            className="report-back-button"
            onClick={() => navigate("/dashboard")}
          >
            <ArrowLeft size={17} />
            Dashboard
          </button>
        </div>

        {/* STATS */}

        <div className="report-metric-grid history-summary-grid">
          <div className="report-metric-card">
            <FileText size={18} />

            <span>Total interviews</span>

            <strong>{items.length}</strong>
          </div>

          <div className="report-metric-card">
            <CheckCircle2 size={18} />

            <span>Completed</span>

            <strong>{completedItems.length}</strong>
          </div>

          <div className="report-metric-card">
            <BarChart3 size={18} />

            <span>Average score</span>

            <strong>
              {averageScore != null ? `${averageScore}/100` : "—"}
            </strong>
          </div>

          <div className="report-metric-card">
            <Target size={18} />

            <span>Scored interviews</span>

            <strong>{scoredItems.length}</strong>
          </div>
        </div>

        {/* ERROR */}

        {error && (
          <div className="report-error-card">
            <h2>History could not be loaded</h2>

            <p>{error}</p>

            <button
              type="button"
              className="report-primary-button"
              onClick={loadHistory}
            >
              Try again
            </button>
          </div>
        )}

        {/* LOADING */}

        {loading && (
          <div className="interview-report-loading">
            <LoaderCircle size={28} className="history-spinner" />

            <h2>Loading your interviews</h2>

            <p>Fetching your saved interview sessions.</p>
          </div>
        )}

        {/* EMPTY */}

        {!loading && !error && items.length === 0 && (
          <section className="report-panel history-empty">
            <div className="report-loading-orb">SH</div>

            <h2>No interviews yet</h2>

            <p>
              Start your first AI interview and your results will appear here.
            </p>

            <button
              type="button"
              className="report-primary-button"
              onClick={() => navigate("/interview/setup")}
            >
              Start an interview
              <ArrowRight size={16} />
            </button>
          </section>
        )}

        {/* HISTORY LIST */}

        {!loading && !error && items.length > 0 && (
          <section className="report-panel">
            <div className="report-panel-heading">
              <div>
                <span className="report-kicker">SESSIONS</span>

                <h2>Previous interviews</h2>
              </div>

              <span className="report-count">{items.length} sessions</span>
            </div>

            <div className="history-list">
              {items.map((item) => {
                const isCompleted = item.status === "completed";

                return (
                  <article className="history-card" key={item.session_id}>
                    <div className="history-card-main">
                      <div className="history-role-icon">
                        <FileText size={19} />
                      </div>

                      <div className="history-card-content">
                        <div className="history-card-title">
                          <h3>{item.role || "Untitled interview"}</h3>

                          <StatusBadge status={item.status} />
                        </div>

                        <div className="history-card-meta">
                          <span>{item.interview_type || "mixed"}</span>

                          <span>·</span>

                          <span>{item.difficulty || "medium"}</span>

                          <span>·</span>

                          <span>{formatDate(item.created_at)}</span>
                        </div>
                      </div>
                    </div>

                    <div className="history-card-score">
                      {item.overall_score != null ? (
                        <>
                          <strong>{item.overall_score}</strong>

                          <span>/100</span>
                        </>
                      ) : (
                        <span className="history-no-score">Not scored</span>
                      )}
                    </div>

                    <div className="history-card-progress">
                      <div>
                        <Clock3 size={14} />

                        <span>
                          {item.evaluated_questions}/{item.total_questions}{" "}
                          evaluated
                        </span>
                      </div>

                      {item.technical_score != null && (
                        <div>
                          <Target size={14} />

                          <span>Technical {item.technical_score}</span>
                        </div>
                      )}
                    </div>

                    <button
                      type="button"
                      className="history-open-button"
                      disabled={!isCompleted}
                      onClick={() => {
                        if (isCompleted) {
                          navigate(`/interview/${item.session_id}/report`);
                        }
                      }}
                    >
                      {isCompleted ? "View report" : "Report unavailable"}

                      {isCompleted && <ArrowRight size={16} />}
                    </button>
                  </article>
                );
              })}
            </div>
          </section>
        )}

        <div className="report-bottom-actions">
          <button
            type="button"
            className="report-primary-button"
            onClick={() => navigate("/interview/setup")}
          >
            Practice another interview
            <ArrowRight size={16} />
          </button>
        </div>
      </main>
    </div>
  );
}
