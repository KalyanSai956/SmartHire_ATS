import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useNavigate, useParams } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

import {
  retryInterviewRequest,
  completeInterviewSession,
  evaluateInterviewAnswer,
  generateInterviewQuestions,
  getAdaptiveNextQuestion,
  getInterviewQuestions,
  getInterviewSession,
  pauseInterviewSession,
  resumeInterviewSession,
  startInterviewSession,
  submitInterviewAnswer,
} from "../services/api";

import {
  clearInterviewDraft,
  loadInterviewDraft,
  saveInterviewDraft,
} from "../utils/interviewRecovery";

import InterviewHeader from "../components/interview/InterviewHeader";
import QuestionPanel from "../components/interview/QuestionPanel";
import VoiceInterviewer from "../components/interview/VoiceInterviewer";
import EvaluationFeedback from "../components/interview/EvaluationFeedback";

export default function InterviewArena() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const { session: authSession } = useAuth();

  const token = authSession?.access_token;

  const [interview, setInterview] = useState(null);
  const [questions, setQuestions] = useState([]);

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const [answer, setAnswer] = useState("");

  const [evaluation, setEvaluation] = useState(null);
  const [adaptiveInfo, setAdaptiveInfo] = useState(null);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [paused, setPaused] = useState(false);

  const [error, setError] = useState("");

  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  const [completed, setCompleted] = useState(false);

  const [isOnline, setIsOnline] = useState(
    typeof navigator !== "undefined" ? navigator.onLine : true,
  );

  const [recovering, setRecovering] = useState(false);

  const [draftRecovered, setDraftRecovered] = useState(false);

  const submissionLockRef = useRef(false);
  const startLockRef = useRef(false);

  const currentQuestion = questions[currentQuestionIndex] || null;

  const totalQuestions =
    interview?.configuration?.question_count || questions.length || 10;

  /*
   * =====================================================
   * LOAD INTERVIEW
   * =====================================================
   */

  const loadInterview = useCallback(async () => {
    if (!token || !sessionId) {
      return;
    }

    try {
      setLoading(true);
      setRecovering(true);
      setError("");

      const sessionData = await retryInterviewRequest(
        () =>
          getInterviewSession({
            sessionId,
            token,
          }),
        {
          retries: 3,
        },
      );

      setInterview(sessionData);

      let existingQuestions = [];

      try {
        const questionData = await retryInterviewRequest(
          () =>
            getInterviewQuestions({
              sessionId,
              token,
            }),
          {
            retries: 3,
          },
        );

        existingQuestions = Array.isArray(questionData)
          ? questionData
          : questionData?.questions || [];
      } catch (questionError) {
        console.error("Failed to load interview questions:", questionError);

        /*
         * IMPORTANT:
         *
         * Do NOT generate questions again when the
         * interview is already active.
         *
         * This prevents duplicate generation after
         * refresh/reconnect.
         */
        if (sessionData.status !== "not_started") {
          throw new Error(
            "Interview questions could not be restored. Please reconnect and try again.",
          );
        }
      }

      /*
       * Only generate questions for a brand-new
       * interview.
       */
      if (
        existingQuestions.length === 0 &&
        sessionData.status === "not_started"
      ) {
        const generated = await generateInterviewQuestions({
          sessionId,
          token,
        });

        existingQuestions = Array.isArray(generated)
          ? generated
          : generated?.questions || [];
      }

      if (existingQuestions.length === 0) {
        throw new Error("No interview questions are available.");
      }

      existingQuestions.sort(
        (a, b) => Number(a.question_order || 0) - Number(b.question_order || 0),
      );

      setQuestions(existingQuestions);

      /*
       * Restore current question.
       */
      const savedNumber = Number(sessionData.current_question_number) || 1;

      const restoredIndex = Math.max(
        0,
        Math.min(savedNumber - 1, existingQuestions.length - 1),
      );

      setCurrentQuestionIndex(restoredIndex);

      /*
       * Restore local answer draft.
       */
      const savedDraft = loadInterviewDraft(sessionId);

      if (
        savedDraft &&
        savedDraft.questionId === existingQuestions[restoredIndex]?.id &&
        typeof savedDraft.answer === "string" &&
        savedDraft.answer.trim()
      ) {
        setAnswer(savedDraft.answer);
        setDraftRecovered(true);
      }

      if (sessionData.status === "paused") {
        setPaused(true);
      }

      if (sessionData.status === "completed") {
        setCompleted(true);
      }

      /*
       * Recover timer from server start time.
       */
      if (sessionData.started_at) {
        const startedAt = new Date(sessionData.started_at).getTime();

        if (!Number.isNaN(startedAt)) {
          const seconds = Math.max(
            0,
            Math.floor((Date.now() - startedAt) / 1000),
          );

          setElapsedSeconds(seconds);
        }
      }
    } catch (err) {
      console.error("Failed to load interview:", err);

      setError(err?.message || "Unable to load the interview.");
    } finally {
      setRecovering(false);
      setLoading(false);
    }
  }, [token, sessionId]);

  useEffect(() => {
    loadInterview();
  }, [loadInterview]);

  /*
   * =====================================================
   * ONLINE / OFFLINE
   * =====================================================
   */

  useEffect(() => {
    function handleOnline() {
      setIsOnline(true);
      setError("");
    }

    function handleOffline() {
      setIsOnline(false);

      setError(
        "Your internet connection was lost. Your current answer is being saved locally.",
      );
    }

    window.addEventListener("online", handleOnline);

    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);

      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  /*
   * =====================================================
   * SAVE ANSWER DRAFT
   * =====================================================
   */

  useEffect(() => {
    if (!sessionId || completed || !currentQuestion) {
      return;
    }

    saveInterviewDraft(sessionId, {
      questionId: currentQuestion.id,
      questionIndex: currentQuestionIndex,
      answer,
    });
  }, [sessionId, currentQuestion?.id, currentQuestionIndex, answer, completed]);

  /*
   * =====================================================
   * TIMER
   * =====================================================
   */

  useEffect(() => {
    if (loading || paused || completed) {
      return undefined;
    }

    const timer = window.setInterval(() => {
      setElapsedSeconds((current) => current + 1);
    }, 1000);

    return () => window.clearInterval(timer);
  }, [loading, paused, completed]);

  /*
   * =====================================================
   * START SESSION
   * =====================================================
   */

  useEffect(() => {
    if (loading || !interview || !token || completed || startLockRef.current) {
      return;
    }

    if (interview.status !== "not_started") {
      return;
    }

    startLockRef.current = true;

    startInterviewSession({
      sessionId,
      token,
    })
      .then((updated) => {
        setInterview(updated);
      })
      .catch((err) => {
        console.error("Failed to start interview:", err);

        setError(err?.message || "Unable to start the interview.");
      })
      .finally(() => {
        startLockRef.current = false;
      });
  }, [loading, interview, token, sessionId, completed]);

  /*
   * =====================================================
   * PROGRESS
   * =====================================================
   */

  const progress = useMemo(() => {
    const configuredCount = Math.max(
      Number(interview?.configuration?.question_count) || 10,
      5,
    );

    return Math.min(
      100,
      Math.round(((currentQuestionIndex + 1) / configuredCount) * 100),
    );
  }, [currentQuestionIndex, interview?.configuration?.question_count]);

  /*
   * =====================================================
   * SUBMIT ANSWER
   * =====================================================
   */

  async function handleSubmitAnswer() {
    if (
      !currentQuestion ||
      !answer.trim() ||
      submitting ||
      submissionLockRef.current ||
      paused ||
      completed ||
      !isOnline
    ) {
      return;
    }

    submissionLockRef.current = true;

    try {
      setSubmitting(true);
      setError("");
      setEvaluation(null);
      setAdaptiveInfo(null);

      /*
       * 1. Save candidate answer.
       */
      const answerResult = await submitInterviewAnswer({
        sessionId,
        questionId: currentQuestion.id,
        answerText: answer.trim(),
        answerSource: "voice",
        token,
      });

      const answerId = answerResult?.id || answerResult?.answer_id;

      if (!answerId) {
        throw new Error("Answer was submitted without an answer ID.");
      }

      /*
       * 2. Evaluate answer.
       */
      const evaluationResult = await evaluateInterviewAnswer({
        sessionId,
        answerId,
        token,
      });

      const evaluationData = evaluationResult?.evaluation || evaluationResult;

      setEvaluation(evaluationData);

      /*
       * 3. Final question.
       */
      const configuredCount = Math.max(
        Number(interview?.configuration?.question_count) || 10,
        5,
      );

      const isLastQuestion = currentQuestionIndex + 1 >= configuredCount;

      if (isLastQuestion) {
        await completeInterviewSession({
          sessionId,
          token,
        });

        clearInterviewDraft(sessionId);

        setCompleted(true);

        return;
      }

      /*
       * 4. Adaptive next question.
       */
      const adaptive = await getAdaptiveNextQuestion({
        sessionId,
        questionId: currentQuestion.id,
        answerId,
        token,
      });

      const nextQuestion = adaptive?.question ? adaptive : adaptive?.data;

      if (!nextQuestion) {
        throw new Error("Adaptive interviewer did not return a next question.");
      }

      const normalizedQuestion = {
        id: nextQuestion.question_id || nextQuestion.id,

        question: nextQuestion.question,

        category: nextQuestion.category,

        difficulty: nextQuestion.difficulty,

        skill: nextQuestion.skill || "",

        expected_topics: nextQuestion.expected_topics || [],

        question_order: nextQuestion.question_order,
      };

      /*
       * Replace an existing question if
       * adaptive generation reused its order.
       */
      setQuestions((current) => {
        const nextOrder = Number(normalizedQuestion.question_order);

        const orderIndex = current.findIndex(
          (item) => Number(item.question_order) === nextOrder,
        );

        if (orderIndex !== -1) {
          const updated = [...current];

          updated[orderIndex] = normalizedQuestion;

          return updated.sort(
            (a, b) =>
              Number(a.question_order || 0) - Number(b.question_order || 0),
          );
        }

        return [...current, normalizedQuestion].sort(
          (a, b) =>
            Number(a.question_order || 0) - Number(b.question_order || 0),
        );
      });

      setAdaptiveInfo(adaptive);

      /*
       * Find the next question by ID after
       * state has been updated.
       */
      setQuestions((current) => {
        const nextIndex = current.findIndex(
          (item) => item.id === normalizedQuestion.id,
        );

        if (nextIndex !== -1) {
          setCurrentQuestionIndex(nextIndex);
        }

        return current;
      });

      setAnswer("");

      clearInterviewDraft(sessionId);

      setDraftRecovered(false);
    } catch (err) {
      console.error("Interview answer submission failed:", err);

      setError(
        err?.message || "Unable to process your answer. Please try again.",
      );
    } finally {
      submissionLockRef.current = false;

      setSubmitting(false);
    }
  }

  /*
   * =====================================================
   * PAUSE / RESUME
   * =====================================================
   */

  async function handlePause() {
    if (!token || completed) {
      return;
    }

    try {
      if (!paused) {
        const result = await pauseInterviewSession({
          sessionId,
          token,
        });

        setInterview(result);
        setPaused(true);
      } else {
        const result = await resumeInterviewSession({
          sessionId,
          token,
        });

        setInterview(result);
        setPaused(false);
      }
    } catch (err) {
      console.error("Interview pause/resume failed:", err);

      setError(err?.message || "Unable to update interview state.");
    }
  }

  /*
   * =====================================================
   * EXIT
   * =====================================================
   */

  function handleExit() {
    const confirmed = window.confirm(
      "Are you sure you want to leave this interview? Your saved progress will remain available.",
    );

    if (confirmed) {
      navigate("/dashboard");
    }
  }

  /*
   * =====================================================
   * LOADING
   * =====================================================
   */

  if (loading) {
    return (
      <div className="arena-page">
        <div className="arena-loading">
          <div className="arena-loading-orb">SH</div>

          <h2>Preparing your interview</h2>

          <p>Loading your personalized questions...</p>

          <div className="arena-loading-bar">
            <span />
          </div>
        </div>
      </div>
    );
  }

  /*
   * =====================================================
   * ERROR
   * =====================================================
   */

  if (error && !interview) {
    return (
      <div className="arena-page">
        <div className="arena-error-screen">
          <span className="arena-error-icon">!</span>

          <h2>Interview could not be loaded</h2>

          <p>{error}</p>

          <div className="arena-error-actions">
            <button
              type="button"
              onClick={loadInterview}
              className="arena-secondary-button"
            >
              Try again
            </button>

            <button
              type="button"
              onClick={() => navigate("/dashboard")}
              className="arena-primary-button"
            >
              Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  /*
   * =====================================================
   * COMPLETED
   * =====================================================
   */

  if (completed) {
    return (
      <div className="arena-page">
        <div className="arena-complete-screen">
          <div className="arena-complete-icon">✓</div>

          <span className="arena-eyebrow">INTERVIEW COMPLETE</span>

          <h1>Interview session completed</h1>

          <p>
            Your answers and evaluations have been saved. Your final interview
            report will be available from your interview history.
          </p>

          {evaluation && (
            <div className="arena-final-score">
              <span>Last response score</span>

              <strong>{evaluation.overall_score}</strong>
            </div>
          )}

          <div className="arena-complete-actions">
            <button
              type="button"
              className="arena-primary-button"
              onClick={() => navigate(`/interview/${sessionId}/report`)}
            >
              View interview report →
            </button>

            <button
              type="button"
              className="arena-secondary-button"
              onClick={() => navigate("/interviews/history")}
            >
              Interview history
            </button>
          </div>
        </div>
      </div>
    );
  }

  /*
   * =====================================================
   * MAIN UI
   * =====================================================
   */

  return (
    <div className="mx-auto max-w-5xl px-6 py-5 arena-page">
      <InterviewHeader
        currentNumber={currentQuestionIndex + 1}
        totalQuestions={Math.max(
          Number(interview?.configuration?.question_count) || 10,
          5,
        )}
        difficulty={
          currentQuestion?.difficulty || interview?.difficulty || "medium"
        }
        category={currentQuestion?.category || "technical"}
        elapsedSeconds={elapsedSeconds}
        onPause={handlePause}
        paused={paused}
      />

      <main className="arena-main">
        <div className="arena-topbar">
          <button
            type="button"
            className="arena-exit-button"
            onClick={handleExit}
          >
            ← Exit interview
          </button>

          <div className="arena-session-info">
            <span>{interview?.role}</span>

            <span className="arena-session-divider">/</span>

            <span>{interview?.interview_type}</span>
          </div>
        </div>

        {error && (
          <div className="arena-inline-error">
            <span>!</span>
            {error}
          </div>
        )}

        {!isOnline && (
          <div className="arena-inline-error">
            <span>!</span>
            You are offline. Your current answer is saved locally.
          </div>
        )}

        {isOnline && recovering && (
          <div className="arena-paused-banner">
            <strong>Reconnecting...</strong>

            <span>Restoring your interview session.</span>
          </div>
        )}

        {draftRecovered && (
          <div className="arena-paused-banner">
            <strong>Draft restored</strong>

            <span>Your previous answer was recovered.</span>
          </div>
        )}

        {paused && (
          <div className="arena-paused-banner">
            <strong>Interview paused</strong>

            <span>Resume when you're ready to continue.</span>
          </div>
        )}

        <div className="arena-layout">
          <div className="arena-primary-column">
            <QuestionPanel
              question={currentQuestion}
              questionNumber={currentQuestionIndex + 1}
            />

            {!evaluation && (
              <VoiceInterviewer
                question={currentQuestion}
                answer={answer}
                onAnswerChange={setAnswer}
                onSubmit={handleSubmitAnswer}
                token={token}
                submitting={submitting}
                disabled={paused || completed || !currentQuestion || !isOnline}
              />
            )}

            {evaluation && (
              <>
                <EvaluationFeedback evaluation={evaluation} />

                {!completed && (
                  <div className="arena-next-panel">
                    <div>
                      <span>ADAPTIVE INTERVIEWER</span>

                      <strong>Next question is ready</strong>

                      {adaptiveInfo?.reason && <p>{adaptiveInfo.reason}</p>}
                    </div>

                    <button
                      type="button"
                      className="arena-primary-button"
                      onClick={() => {
                        setEvaluation(null);

                        setAdaptiveInfo(null);
                      }}
                    >
                      Continue interview →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          <aside className="arena-side-column">
            <div className="arena-side-card">
              <div className="arena-side-heading">
                <span>SESSION</span>

                <strong>{progress}%</strong>
              </div>

              <div className="arena-side-progress">
                <div
                  style={{
                    width: `${progress}%`,
                  }}
                />
              </div>

              <div className="arena-side-stat">
                <span>Target role</span>

                <strong>{interview?.role || "Not specified"}</strong>
              </div>

              <div className="arena-side-stat">
                <span>Interview type</span>

                <strong>{interview?.interview_type || "Mixed"}</strong>
              </div>

              <div className="arena-side-stat">
                <span>Difficulty</span>

                <strong>
                  {currentQuestion?.difficulty ||
                    interview?.difficulty ||
                    "Medium"}
                </strong>
              </div>
            </div>

            <div className="arena-side-card arena-ai-card">
              <div className="arena-ai-icon">✦</div>

              <span>ADAPTIVE AI</span>

              <h3>Your next question responds to your performance.</h3>

              <p>
                SmartHire evaluates every response and adjusts the next question
                based on demonstrated strengths and gaps.
              </p>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
