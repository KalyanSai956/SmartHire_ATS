import { useEffect, useRef, useState } from "react";
import { transcribeInterviewAudio } from "../../services/api";

export default function VoiceControls({
  text,
  onTranscriptChange,
  token,
  disabled = false,
  voiceMode = false,
  autoRecord = false,
  onRecordingStateChange,
}) {
  const mediaRecorderRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);

  const browserRecognitionRef = useRef(null);
  const browserListeningRef = useRef(false);
  const shouldKeepBrowserListeningRef = useRef(false);

  const textRef = useRef(text || "");

  const autoRecordTriggeredRef = useRef(false);

  const timerRef = useRef(null);

  const [isSupported, setIsSupported] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [error, setError] = useState("");

  /*
   * Keep the latest text available to browser
   * speech-recognition callbacks.
   */
  useEffect(() => {
    textRef.current = text || "";
  }, [text]);

  /*
   * Check browser recording support.
   */
  useEffect(() => {
    const supported =
      Boolean(navigator.mediaDevices?.getUserMedia) &&
      Boolean(window.MediaRecorder);

    setIsSupported(supported);
  }, []);

  /*
   * Create browser SpeechRecognition once.
   *
   * This is used for LIVE transcription while
   * MediaRecorder captures the actual audio.
   */
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      return undefined;
    }

    const recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      browserListeningRef.current = true;

      console.log("[Voice] Browser live transcription started");
    };

    recognition.onresult = (event) => {
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];

        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        }
      }

      const cleanTranscript = finalTranscript.trim();

      if (!cleanTranscript) {
        return;
      }

      const currentText = textRef.current || "";

      const separator = currentText && !currentText.endsWith(" ") ? " " : "";

      const updatedText = currentText + separator + cleanTranscript;

      textRef.current = updatedText;

      onTranscriptChange(updatedText);
    };

    recognition.onerror = (event) => {
      console.warn("[Voice] Browser recognition error:", event.error);

      /*
       * Don't stop the actual recording because
       * browser recognition failed.
       *
       * MediaRecorder continues independently.
       */
      if (event.error === "not-allowed" || event.error === "audio-capture") {
        shouldKeepBrowserListeningRef.current = false;
      }
    };

    recognition.onend = () => {
      browserListeningRef.current = false;

      /*
       * Chrome can stop SpeechRecognition
       * even while the user is still recording.
       *
       * Restart it while the user has not pressed Stop.
       */
      if (shouldKeepBrowserListeningRef.current) {
        window.setTimeout(() => {
          if (
            shouldKeepBrowserListeningRef.current &&
            !browserListeningRef.current
          ) {
            try {
              recognition.start();
            } catch {
              // Already starting/running.
            }
          }
        }, 150);
      }
    };

    browserRecognitionRef.current = recognition;

    return () => {
      shouldKeepBrowserListeningRef.current = false;

      try {
        recognition.abort();
      } catch {
        // Already stopped.
      }

      browserRecognitionRef.current = null;
    };
  }, [onTranscriptChange]);

  /*
   * Timer.
   */
  function startTimer() {
    setRecordingSeconds(0);

    timerRef.current = window.setInterval(() => {
      setRecordingSeconds((seconds) => seconds + 1);
    }, 1000);
  }

  function stopTimer() {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);

      timerRef.current = null;
    }
  }

  function formatDuration() {
    const minutes = Math.floor(recordingSeconds / 60);

    const seconds = recordingSeconds % 60;

    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(
      2,
      "0",
    )}`;
  }

  /*
   * Start browser live recognition.
   */
  function startBrowserRecognition() {
    const recognition = browserRecognitionRef.current;

    if (!recognition || browserListeningRef.current) {
      return;
    }

    shouldKeepBrowserListeningRef.current = true;

    try {
      recognition.start();
    } catch {
      // Recognition may already be starting.
    }
  }

  /*
   * Stop browser live recognition.
   */
  function stopBrowserRecognition() {
    shouldKeepBrowserListeningRef.current = false;

    const recognition = browserRecognitionRef.current;

    if (!recognition) {
      return;
    }

    try {
      recognition.stop();
    } catch {
      // Already stopped.
    }

    browserListeningRef.current = false;
  }

  /*
   * START RECORDING
   */
  async function startRecording() {
    if (disabled || isRecording || isProcessing) {
      return;
    }

    setError("");

    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError("Your browser does not support microphone recording.");

      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      mediaStreamRef.current = stream;

      audioChunksRef.current = [];

      const mimeTypes = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];

      const supportedMime = mimeTypes.find((mime) =>
        MediaRecorder.isTypeSupported(mime),
      );

      const recorder = supportedMime
        ? new MediaRecorder(stream, {
            mimeType: supportedMime,
          })
        : new MediaRecorder(stream);

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onerror = (event) => {
        console.error("[Voice] MediaRecorder error:", event);

        setError("Audio recording failed. Please try again.");
      };

      recorder.onstop = async () => {
        stopTimer();

        stream.getTracks().forEach((track) => track.stop());

        mediaStreamRef.current = null;

        const chunks = audioChunksRef.current;

        audioChunksRef.current = [];

        if (!chunks.length) {
          setIsProcessing(false);

          setError("No audio was captured.");

          return;
        }

        const audioBlob = new Blob(chunks, {
          type: recorder.mimeType || "audio/webm",
        });

        setIsProcessing(true);
        setError("");

        try {
          if (!token) {
            throw new Error("Authentication token is missing.");
          }

          console.log("[Voice] Sending recording for final transcription...");

          const result = await transcribeInterviewAudio({
            audioBlob,
            token,
          });

          const transcript = result?.transcript?.trim();

          if (!transcript) {
            throw new Error("No speech was detected.");
          }

          /*
           * Final backend transcription replaces
           * the live browser transcript.
           *
           * This prevents duplicated text.
           */
          textRef.current = transcript;

          onTranscriptChange(transcript);

          setError("");

          console.log("[Voice] Final transcription received.");
        } catch (transcriptionError) {
          console.warn(
            "[Voice] Backend transcription failed:",
            transcriptionError,
          );

          /*
           * Keep whatever browser live
           * transcription managed to capture.
           */
          if (!textRef.current?.trim()) {
            setError(
              "Transcription failed. Please type your answer or record again.",
            );
          } else {
            setError(
              "Final transcription failed. Your live transcript was preserved.",
            );
          }
        } finally {
          setIsProcessing(false);
        }
      };

      mediaRecorderRef.current = recorder;

      recorder.start(1000);

      setIsRecording(true);

      startTimer();

      /*
       * Start live browser transcript.
       */
      startBrowserRecognition();

      console.log("[Voice] Recording started.");
      onRecordingStateChange?.(true);
    } catch (error) {
      console.error("[Voice] Microphone access failed:", error);

      setError(
        "Microphone access was denied or unavailable. Please allow microphone access.",
      );
    }
  }

  /*
   * STOP RECORDING
   *
   * Silence does NOT call this function.
   * Only the user pressing Stop calls it.
   */
  function stopRecording() {
    if (!isRecording) {
      return;
    }

    stopBrowserRecognition();

    stopTimer();

    const recorder = mediaRecorderRef.current;

    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }

    setIsRecording(false);

    console.log("[Voice] Recording stopped.");
    onRecordingStateChange?.(false);
  }

  /*
   * Automatically start recording after
   * the interviewer finishes speaking.
   */
  useEffect(() => {
    if (
      !voiceMode ||
      !autoRecord ||
      disabled ||
      isRecording ||
      isProcessing ||
      autoRecordTriggeredRef.current
    ) {
      return undefined;
    }

    autoRecordTriggeredRef.current = true;

    const timer = window.setTimeout(() => {
      startRecording();
    }, 400);

    return () => {
      window.clearTimeout(timer);
    };
  }, [voiceMode, autoRecord, disabled, isRecording, isProcessing]);

  /*
   * Reset auto-record guard when AI is no longer
   * waiting for the candidate.
   */
  useEffect(() => {
    if (!autoRecord) {
      autoRecordTriggeredRef.current = false;
    }
  }, [autoRecord]);

  /*
   * Cleanup.
   */
  useEffect(() => {
    return () => {
      stopTimer();

      shouldKeepBrowserListeningRef.current = false;

      if (browserRecognitionRef.current) {
        try {
          browserRecognitionRef.current.abort();
        } catch {
          // Already stopped.
        }
      }

      if (
        mediaRecorderRef.current &&
        mediaRecorderRef.current.state !== "inactive"
      ) {
        try {
          mediaRecorderRef.current.stop();
        } catch {
          // Already stopped.
        }
      }

      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  if (!isSupported) {
    return (
      <div className="voice-controls">
        <div className="voice-unsupported">
          Voice recording is not supported in this browser.
        </div>
      </div>
    );
  }

  return (
    <div className="voice-controls">
      {voiceMode ? (
        <>
          {isRecording && (
            <button
              type="button"
              className="voice-button listening"
              onClick={stopRecording}
              disabled={isProcessing}
            >
              ⏹ Stop answer
            </button>
          )}

          {!isRecording && !isProcessing && autoRecord && (
            <div className="voice-waiting">🎙️ Preparing microphone...</div>
          )}
        </>
      ) : (
        /*
         * This branch is retained temporarily so
         * other components using VoiceControls
         * do not break.
         *
         * InterviewArena itself will only use
         * voiceMode.
         */
        <div className="voice-actions">
          {!isRecording ? (
            <button
              type="button"
              className="voice-button"
              onClick={startRecording}
              disabled={disabled || isProcessing}
            >
              🎙️ Start recording
            </button>
          ) : (
            <button
              type="button"
              className="voice-button listening"
              onClick={stopRecording}
              disabled={isProcessing}
            >
              ⏹ Stop recording
            </button>
          )}
        </div>
      )}

      {voiceMode && isRecording && (
        <div className="voice-status">
          <span className="voice-status-dot" />
          Listening · {formatDuration()}
          <span>You can pause and think.</span>
        </div>
      )}

      {isProcessing && (
        <div className="voice-status">
          <span className="voice-status-dot" />
          Transcribing your answer...
        </div>
      )}

      {error && <div className="voice-message">{error}</div>}
    </div>
  );
}
