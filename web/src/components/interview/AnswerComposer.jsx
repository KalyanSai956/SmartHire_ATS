import { useEffect, useRef } from "react";
import VoiceControls from "./VoiceControls";
import { synthesizeInterviewSpeech } from "../../services/api";

export default function AnswerComposer({
  value,
  onChange,
  onSubmit,
  submitting,
  disabled,
  token,
}) {
  const textareaRef = useRef(null);

  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  function handleKeyDown(event) {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      event.preventDefault();

      if (value.trim() && !submitting && !disabled) {
        onSubmit();
      }
    }
  }

  const characterCount = value.length;

  async function handleSpeak(text) {
    if (!text?.trim()) {
      return;
    }

    try {
      console.log("[Voice] Requesting backend TTS...");

      const audioBlob = await synthesizeInterviewSpeech({
        text,
        token,
      });

      const audioUrl = URL.createObjectURL(audioBlob);

      const audio = new Audio(audioUrl);

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = () => {
        URL.revokeObjectURL(audioUrl);
        throw new Error("Generated audio could not be played.");
      };

      await audio.play();

      console.log("[Voice] Backend TTS playback started");
    } catch (error) {
      console.warn("[Voice] Backend TTS failed. Using browser TTS.", error);

      /*
       * Browser TTS fallback.
       */
      if ("speechSynthesis" in window) {
        const utterance = new SpeechSynthesisUtterance(text);

        utterance.lang = "en-US";
        utterance.rate = 0.95;

        window.speechSynthesis.cancel();

        window.speechSynthesis.speak(utterance);
      }
    }
  }

  return (
    <section className="arena-answer-card">
      <div className="arena-answer-heading">
        <div>
          <span className="arena-answer-label">YOUR RESPONSE</span>

          <h2>Take your time and explain your reasoning.</h2>
        </div>

        <span className="arena-answer-mode">TEXT MODE</span>
      </div>

      <textarea
        ref={textareaRef}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        disabled={disabled || submitting}
        placeholder="Type your answer here..."
        maxLength={10000}
        rows={9}
      />

      <VoiceControls
        text={value}
        onTranscriptChange={onChange}
        disabled={disabled || submitting}
        token={token}
        onSpeak={handleSpeak}
      />

      <div className="arena-answer-footer">
        <span>{characterCount.toLocaleString()} / 10,000</span>

        <span>Ctrl + Enter to submit</span>
      </div>

      <button
        type="button"
        className="arena-submit-button"
        onClick={onSubmit}
        disabled={disabled || submitting || !value.trim()}
      >
        {submitting ? (
          <>
            <span className="arena-button-spinner" />
            Evaluating response...
          </>
        ) : (
          <>
            Submit answer
            <span>→</span>
          </>
        )}
      </button>
    </section>
  );
}
