export default function InterviewHeader({
  currentNumber,
  totalQuestions,
  difficulty,
  category,
  elapsedSeconds,
  onPause,
  paused,
}) {
  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;

  const formattedTime = `${String(minutes).padStart(
    2,
    "0",
  )}:${String(seconds).padStart(2, "0")}`;

  return (
    <header className="arena-header">
      <div className="arena-header-left">
        <div className="arena-brand-mark">SH</div>

        <div>
          <span className="arena-eyebrow">INTERVIEW ARENA</span>

          <strong className="arena-title">Live Interview</strong>
        </div>
      </div>

      <div className="arena-header-center">
        <div className="arena-progress-label">
          <span>Question {currentNumber}</span>

          <span>/ {totalQuestions}</span>
        </div>

        <div className="arena-progress-track">
          <div
            className="arena-progress-fill"
            style={{
              width: `${Math.min(
                100,
                (currentNumber / totalQuestions) * 100,
              )}%`,
            }}
          />
        </div>
      </div>

      <div className="arena-header-right">
        <div className="arena-timer">
          <span className="arena-timer-dot" />
          {formattedTime}
        </div>

        <button type="button" className="arena-pause-button" onClick={onPause}>
          {paused ? "Resume" : "Pause"}
        </button>
      </div>
    </header>
  );
}
