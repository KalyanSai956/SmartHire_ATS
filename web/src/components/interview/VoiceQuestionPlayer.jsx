import React, { useEffect, useState } from "react";

export default function VoiceQuestionPlayer({ question, enabled = true }) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [supported, setSupported] = useState(true);

  useEffect(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) {
      setSupported(false);
    }
  }, []);

  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel();
    };
  }, []);

  const speakQuestion = () => {
    if (!enabled || !supported || !question?.trim()) {
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(question);

    utterance.lang = "en-US";
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onstart = () => {
      setIsSpeaking(true);
    };

    utterance.onend = () => {
      setIsSpeaking(false);
    };

    utterance.onerror = () => {
      setIsSpeaking(false);
    };

    window.speechSynthesis.speak(utterance);
  };

  const stopSpeaking = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  };

  if (!supported) {
    return null;
  }

  return (
    <div className="voice-question-player">
      {!isSpeaking ? (
        <button
          type="button"
          className="voice-button"
          onClick={speakQuestion}
          disabled={!enabled || !question}
        >
          🔊 Hear question
        </button>
      ) : (
        <button
          type="button"
          className="voice-button listening"
          onClick={stopSpeaking}
        >
          ⏹ Stop voice
        </button>
      )}
    </div>
  );
}
