import { Eye, FileText, Trash2, Loader2 } from "lucide-react";

import { Link } from "react-router-dom";

import {
  formatDate,
  getAtsScore,
  getJdMatch,
  normalizeHistory,
  scoreStatus,
} from "../utils/analysis";

export default function AnalysisTable({
  items,
  emptyText = "No analyses yet.",
  onDelete,
  deletingId = null,
}) {
  const rows = normalizeHistory(items);

  /* =====================================================
     EMPTY STATE
     ===================================================== */

  if (!rows.length) {
    return (
      <div className="empty-state">
        <span className="empty-icon">
          <FileText size={18} />
        </span>

        <strong>No analyses yet</strong>

        <span>{emptyText}</span>

        <Link to="/analyze" className="text-link">
          Analyze a resume
        </Link>
      </div>
    );
  }

  /* =====================================================
     TABLE
     ===================================================== */

  return (
    <div className="analysis-table-wrap">
      <table className="analysis-table">
        <thead>
          <tr>
            <th>Resume</th>

            <th>ATS Score</th>

            <th>JD Match</th>

            <th>Date</th>

            <th className="actions-column">Actions</th>
          </tr>
        </thead>

        <tbody>
          {rows.map((item) => {
            const score = getAtsScore(item.result);

            const match = getJdMatch(item.result);

            const itemId = item.id;

            const isDeleting = String(deletingId) === String(itemId);

            return (
              <tr key={itemId ?? item.filename}>
                {/* ======================================
                    RESUME
                ====================================== */}

                <td>
                  <div className="resume-name">
                    <span className="file-icon">
                      <FileText size={15} />
                    </span>

                    <span className="resume-name-text" title={item.filename}>
                      {item.filename}
                    </span>
                  </div>
                </td>

                {/* ======================================
                    ATS SCORE
                ====================================== */}

                <td>
                  <span className={`score-text ${scoreStatus(score)}`}>
                    {score || "—"}
                  </span>
                </td>

                {/* ======================================
                    JD MATCH
                ====================================== */}

                <td>
                  <span className="match-text">
                    {match ? `${Math.round(match)}%` : "—"}
                  </span>
                </td>

                {/* ======================================
                    DATE
                ====================================== */}

                <td className="muted-cell">{formatDate(item.createdAt)}</td>

                {/* ======================================
                    ACTIONS
                ====================================== */}

                <td>
                  <div className="history-actions">
                    {/* VIEW */}

                    {itemId ? (
                      <Link
                        to={`/analysis/${itemId}`}
                        state={{
                          analysis: item.result,

                          filename: item.filename,
                        }}
                        className="history-action view"
                        title="View analysis"
                        aria-label="View analysis"
                      >
                        <Eye size={16} />
                      </Link>
                    ) : null}

                    {/* DELETE */}

                    {itemId && onDelete ? (
                      <button
                        type="button"
                        className="history-action delete"
                        title="Delete analysis"
                        aria-label="Delete analysis"
                        disabled={isDeleting}
                        onClick={() => onDelete(itemId)}
                      >
                        {isDeleting ? (
                          <Loader2 size={16} className="spin" />
                        ) : (
                          <Trash2 size={16} />
                        )}
                      </button>
                    ) : null}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
