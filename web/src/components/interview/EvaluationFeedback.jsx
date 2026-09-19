function Score({ label, value }) {
  return (
    <div className="arena-score">
      <span>{label}</span>

      <strong>{value}</strong>
    </div>
  );
}

export default function EvaluationFeedback({ evaluation }) {
  if (!evaluation) {
    return null;
  }

  return (
    <section className="arena-evaluation-card">
      <div className="arena-evaluation-header">
        <div>
          <span className="arena-answer-label">AI EVALUATION</span>

          <h2>Response analysis</h2>
        </div>

        <div className="arena-overall-score">
          <span>Overall</span>

          <strong>{evaluation.overall_score}</strong>
        </div>
      </div>

      <div className="arena-score-grid">
        <Score label="Technical" value={evaluation.technical_score} />

        <Score label="Relevance" value={evaluation.relevance_score} />

        <Score label="Clarity" value={evaluation.clarity_score} />

        <Score label="Depth" value={evaluation.depth_score} />
      </div>

      {evaluation.feedback && (
        <div className="arena-feedback">
          <span>FEEDBACK</span>

          <p>{evaluation.feedback}</p>
        </div>
      )}

      {evaluation.strengths?.length > 0 && (
        <div className="arena-feedback-list">
          <span>STRENGTHS</span>

          <ul>
            {evaluation.strengths.map((item, index) => (
              <li key={index}>
                <span>+</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {evaluation.weaknesses?.length > 0 && (
        <div className="arena-feedback-list">
          <span>AREAS TO IMPROVE</span>

          <ul>
            {evaluation.weaknesses.map((item, index) => (
              <li key={index}>
                <span>→</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
