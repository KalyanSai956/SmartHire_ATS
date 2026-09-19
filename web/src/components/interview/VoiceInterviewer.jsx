import { useEffect, useRef, useState } from "react";
import { synthesizeInterviewSpeech } from "../../services/api";
import VoiceControls from "./VoiceControls";

export default function VoiceInterviewer({
  question,
  answer,
  onAnswerChange,
  onSubmit,
  token,
  disabled = false,
  submitting = false,
  onRecordingStateChange,
}) {
  const [phase, setPhase] = useState("idle");
  const [ttsError, setTtsError] = useState("");
  const [voiceStarted, setVoiceStarted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const audioRef = useRef(null);
  const audioUrlRef = useRef(null);
  const spokenQuestionIdRef = useRef(null);

  /*
   * ---------------------------------------------------------
   * SPEAK QUESTION
   * ---------------------------------------------------------
   */
  async function speakQuestion() {
    if (!question?.question || !token) {
      return;
    }

    setTtsError("");
    setPhase("speaking");
    setIsRecording(false);

    try {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
        audioRef.current = null;
      }

      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
        audioUrlRef.current = null;
      }

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }

      const audioBlob = await synthesizeInterviewSpeech({
        text: question.question,
        token,
      });

      if (!audioBlob || audioBlob.size === 0) {
        throw new Error("TTS returned empty audio.");
      }

      const audioUrl = URL.createObjectURL(audioBlob);

      audioUrlRef.current = audioUrl;

      const audio = new Audio(audioUrl);

      audioRef.current = audio;
      audio.preload = "auto";

      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);

        audioUrlRef.current = null;
        audioRef.current = null;

        /*
         * AI has finished speaking.
         *
         * VoiceControls receives autoRecord=true
         * through phase === "listening" and automatically
         * starts the microphone.
         */
        setPhase("listening");
      };

      audio.onerror = () => {
        console.warn("[Voice Interviewer] Backend audio playback failed.");

        URL.revokeObjectURL(audioUrl);

        audioUrlRef.current = null;
        audioRef.current = null;

        speakWithBrowser();
      };

      await audio.play();
    } catch (error) {
      console.warn("[Voice Interviewer] Backend TTS failed:", error);

      /*
       * Browser TTS fallback.
       */
      speakWithBrowser();
    }
  }

  /*
   * ---------------------------------------------------------
   * BROWSER TTS FALLBACK
   * ---------------------------------------------------------
   */
  function speakWithBrowser() {
    if (!question?.question) {
      setPhase("ready");
      return;
    }

    if (!("speechSynthesis" in window)) {
      setPhase("ready");

      setTtsError(
        "Voice playback is unavailable. You can still read the question and answer.",
      );

      return;
    }

    try {
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(question.question);

      utterance.lang = "en-US";
      utterance.rate = 0.95;
      utterance.pitch = 1;

      utterance.onstart = () => {
        console.log("[Voice Interviewer] Browser TTS started");

        setTtsError("");
        setPhase("speaking");
        setIsRecording(false);
      };

      utterance.onend = () => {
        console.log("[Voice Interviewer] Browser TTS finished");

        setPhase("listening");
      };

      utterance.onerror = (event) => {
        console.error("[Voice Interviewer] Browser TTS error:", event);

        setPhase("ready");

        setTtsError(
          "The interviewer could not speak this question. Check your browser audio output.",
        );
      };

      window.setTimeout(() => {
        window.speechSynthesis.speak(utterance);
      }, 50);
    } catch (error) {
      console.error("[Voice Interviewer] Browser TTS failed:", error);

      setPhase("ready");

      setTtsError(
        "Voice playback is unavailable. You can still read the question and answer.",
      );
    }
  }

  /*
   * ---------------------------------------------------------
   * START VOICE INTERVIEW
   * ---------------------------------------------------------
   *
   * The first voice interaction must come from the user.
   * This avoids Chrome autoplay restrictions.
   */
  async function handleStartVoiceInterview() {
    if (disabled || submitting || !question?.question || !token) {
      return;
    }

    setVoiceStarted(true);

    spokenQuestionIdRef.current = question.id;

    await speakQuestion();
  }

  /*
   * ---------------------------------------------------------
   * SUBSEQUENT QUESTIONS
   * ---------------------------------------------------------
   *
   * Adaptive questions are spoken automatically once the
   * first voice interview has been started.
   */
  useEffect(() => {
    if (
      !voiceStarted ||
      !question?.id ||
      disabled ||
      submitting ||
      spokenQuestionIdRef.current === question.id
    ) {
      return;
    }

    spokenQuestionIdRef.current = question.id;

    /*
     * Clear the previous answer before the new question.
     */
    onAnswerChange("");

    setIsRecording(false);
    setPhase("speaking");

    const timer = window.setTimeout(() => {
      speakQuestion();
    }, 500);

    return () => {
      window.clearTimeout(timer);
    };
  }, [question?.id, voiceStarted, disabled, submitting]);

  /*
   * ---------------------------------------------------------
   * IMPORTANT:
   * RECORDING STATE
   * ---------------------------------------------------------
   *
   * We keep recording state separately from the interview
   * phase.
   *
   * Why?
   *
   * VoiceControls calls onRecordingStateChange(false)
   * BEFORE Groq Whisper finishes.
   *
   * Therefore we cannot check `answer` inside that callback.
   */
  function handleRecordingStateChange(recording) {
    setIsRecording(recording);

    if (recording) {
      /*
       * Microphone is active.
       */
      setPhase("listening");
    }

    onRecordingStateChange?.(recording);
  }

  /*
   * ---------------------------------------------------------
   * TRANSCRIPTION → ANSWER READY
   * ---------------------------------------------------------
   *
   * This is the critical fix.
   *
   * During recording:
   *
   *     isRecording = true
   *     answer changes continuously
   *
   * We DO NOT switch to answer-ready.
   *
   * After Stop:
   *
   *     isRecording = false
   *
   * Groq Whisper then updates `answer`.
   *
   * This effect detects that combination and changes
   * the phase to answer-ready.
   */
  useEffect(() => {
    if (
      voiceStarted &&
      !isRecording &&
      answer.trim() &&
      phase === "listening"
    ) {
      console.log("[Voice Interviewer] Final transcript ready.");

      setPhase("answer-ready");
    }
  }, [answer, isRecording, voiceStarted, phase]);

  /*
   * ---------------------------------------------------------
   * CLEANUP
   * ---------------------------------------------------------
   */
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
        audioRef.current = null;
      }

      if (audioUrlRef.current) {
        URL.revokeObjectURL(audioUrlRef.current);
        audioUrlRef.current = null;
      }

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  /*
   * ---------------------------------------------------------
   * INITIAL STATE
   * ---------------------------------------------------------
   */
  if (!voiceStarted) {
    return (
      <section className="voice-interviewer-card">
        <div className="voice-interviewer-header">
          <div>
            <span className="arena-answer-label">AI VOICE INTERVIEWER</span>

            <h2>Ready for your voice interview?</h2>
          </div>

          <div className="voice-interviewer-state">🎙️ Ready</div>
        </div>

        <div className="voice-interviewer-question">
          <span>INTERVIEWER</span>

          <p>{question?.question}</p>
        </div>

        <button
          type="button"
          className="voice-start-interview-button"
          onClick={handleStartVoiceInterview}
          disabled={disabled || submitting}
        >
          🔊 Start voice interview
        </button>

        <div className="voice-interviewer-hint">
          The AI interviewer will speak the question. Recording will
          automatically start when it finishes.
        </div>
      </section>
    );
  }

  /*
   * ---------------------------------------------------------
   * ACTIVE INTERVIEW
   * ---------------------------------------------------------
   */
  return (
    <section className="voice-interviewer-card">
      <div className="voice-interviewer-header">
        <div>
          <span className="arena-answer-label">AI VOICE INTERVIEWER</span>

          <h2>
            {phase === "speaking"
              ? "Interviewer is speaking..."
              : phase === "listening"
                ? "Your turn"
                : phase === "answer-ready"
                  ? "Answer captured"
                  : phase === "ready"
                    ? "Voice unavailable"
                    : "Preparing..."}
          </h2>
        </div>

        <div className="voice-interviewer-state">
          {phase === "speaking" && "🔊 Speaking"}
          {phase === "listening" && "🎙️ Listening"}
          {phase === "answer-ready" && "✓ Captured"}
          {phase === "ready" && "Voice unavailable"}
          {phase === "idle" && "Preparing"}
        </div>
      </div>

      <div className="voice-interviewer-question">
        <span>INTERVIEWER</span>

        <p>{question?.question}</p>
      </div>

      {ttsError && <div className="voice-interviewer-warning">{ttsError}</div>}

      <div className="voice-answer-section">
        <div className="voice-answer-heading">
          <span className="arena-answer-label">YOUR RESPONSE</span>

          <span className="arena-answer-mode">VOICE TRANSCRIPT</span>
        </div>

        <textarea
          value={answer}
          onChange={(event) => onAnswerChange(event.target.value)}
          disabled={disabled || submitting || phase === "speaking"}
          placeholder={
            phase === "listening"
              ? "Start speaking... your answer will appear here."
              : "Your spoken answer will appear here..."
          }
          maxLength={10000}
          rows={9}
        />

        <div className="arena-answer-footer">
          <span>{answer.length.toLocaleString()} / 10,000</span>

          <span>
            {phase === "listening"
              ? "Speak naturally — you can pause and think."
              : phase === "answer-ready"
                ? "Review your answer before submitting."
                : "Your transcript will appear here."}
          </span>
        </div>
      </div>

      <VoiceControls
        text={answer}
        onTranscriptChange={onAnswerChange}
        token={token}
        disabled={disabled || submitting || phase === "speaking"}
        voiceMode
        autoRecord={phase === "listening"}
        onRecordingStateChange={handleRecordingStateChange}
      />

      <button
        type="button"
        className="arena-submit-button"
        onClick={onSubmit}
        disabled={
          disabled || submitting || !answer.trim() || phase !== "answer-ready"
        }
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
