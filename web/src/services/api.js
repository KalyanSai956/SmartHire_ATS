const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

import { retryRequest } from "./apiRetry";
async function request(
  path,
  { token, ...options } = {}
) {
  const headers = new Headers(
    options.headers || {}
  );

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${path}`,
    {
      ...options,
      headers,
    }
  );

  const contentType =
    response.headers.get("content-type") || "";


  if (!response.ok) {
    let message =
      `Request failed (${response.status})`;

    if (
      contentType.includes(
        "application/json"
      )
    ) {
      const data =
        await response
          .json()
          .catch(() => null);

      message =
        data?.detail ||
        message;

    } else {
      const text =
        await response
          .text()
          .catch(() => "");

      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }


  if (
    contentType.includes(
      "application/json"
    )
  ) {
    return response.json();
  }


  return response.text();
}

export async function retryInterviewRequest(
  operation,
  options = {},
) {
  return retryRequest(operation, {
    retries: 3,
    baseDelay: 700,
    ...options,
  });
}
/* =====================================================
   HEALTH
   ===================================================== */

export function healthCheck() {
  return request(
    "/api/v1/health"
  );
}


/* =====================================================
   HISTORY
   ===================================================== */

export function getHistory(token) {
  return request(
    "/api/v1/history",
    {
      token,
    }
  );
}


/* =====================================================
   DELETE HISTORY
   ===================================================== */

export function deleteHistoryEntry(
  id,
  token
) {
  return request(
    `/api/v1/history/${id}`,
    {
      method: "DELETE",
      token,
    }
  );
}


/*
 * Keep this alias because your History.jsx
 * currently imports deleteHistory.
 */
export function deleteHistory(
  id,
  token
) {
  return deleteHistoryEntry(
    id,
    token
  );
}


/* =====================================================
   RESUME ANALYSIS
   ===================================================== */

export function analyzeResume({
  file,
  jobDescription,
  token,
}) {
  const formData =
    new FormData();

  formData.append(
    "resume",
    file
  );

  formData.append(
    "job_description",
    jobDescription || ""
  );


  return request(
    "/api/v1/analyze-resume",
    {
      method: "POST",
      body: formData,
      token,
    }
  );
}
export function createInterviewSession({
  role,
  jobDescription,
  interviewType,
  difficulty,
  configuration,
  token,
}) {
  return request("/api/v1/interviews", {
    method: "POST",
    token,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      role,
      job_description: jobDescription,
      interview_type: interviewType,
      difficulty,
      configuration: {
        question_count: configuration.questionCount,
        duration_minutes: configuration.durationMinutes,
        focus_areas: configuration.focusAreas,
        include_coding: configuration.includeCoding,
        include_system_design: configuration.includeSystemDesign,
      },
    }),
  });
}
export function getInterviewSession({
  sessionId,
  token,
}) {
  return request(`/api/v1/interviews/${sessionId}`, {
    method: "GET",
    token,
  });
}

export function startInterviewSession({
  sessionId,
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/start`,
    {
      method: "POST",
      token,
    }
  );
}

/* =====================================================
   INTERVIEW — QUESTIONS
   ===================================================== */

export function generateInterviewQuestions({
  sessionId,
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/questions/generate`,
    {
      method: "POST",
      token,
    }
  );
}


/* =====================================================
   INTERVIEW — GET QUESTIONS
   ===================================================== */

export function getInterviewQuestions({
  sessionId,
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/questions`,
    {
      method: "GET",
      token,
    }
  );
}


/* =====================================================
   INTERVIEW — SUBMIT ANSWER
   ===================================================== */

export function submitInterviewAnswer({
  sessionId,
  questionId,
  answerText,
  answerSource = "text",
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/questions/${questionId}/answer`,
    {
      method: "POST",
      token,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        answer_text: answerText,
        answer_source: answerSource,
      }),
    }
  );
}


/* =====================================================
   INTERVIEW — EVALUATE ANSWER
   ===================================================== */

export function evaluateInterviewAnswer({
  sessionId,
  answerId,
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/answers/${answerId}/evaluate`,
    {
      method: "POST",
      token,
    }
  );
}


/* =====================================================
   INTERVIEW — ADAPTIVE NEXT QUESTION
   ===================================================== */

export function getAdaptiveNextQuestion({
  sessionId,
  questionId,
  answerId,
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/questions/${questionId}/adaptive-next?answer_id=${encodeURIComponent(
      answerId
    )}`,
    {
      method: "POST",
      token,
    }
  );
}


/* =====================================================
   INTERVIEW — PAUSE
   ===================================================== */

export function pauseInterviewSession({
  sessionId,
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/pause`,
    {
      method: "POST",
      token,
    }
  );
}


/* =====================================================
   INTERVIEW — RESUME
   ===================================================== */

export function resumeInterviewSession({
  sessionId,
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/resume`,
    {
      method: "POST",
      token,
    }
  );
}


/* =====================================================
   INTERVIEW — COMPLETE
   ===================================================== */

export function completeInterviewSession({
  sessionId,
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/complete`,
    {
      method: "POST",
      token,
    }
  );
}
/* =====================================================
   HISTORY PDF
   ===================================================== */

export async function getHistoryPdf(
  id,
  token
) {
  const response =
    await fetch(
      `${API_BASE_URL}/api/v1/history/${id}/pdf`,
      {
        headers: token
          ? {
              Authorization:
                `Bearer ${token}`,
            }
          : {},
      }
    );


  if (!response.ok) {
    const data =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      data?.detail ||
        `PDF request failed (${response.status})`
    );
  }


  return response.blob();
}


/* =====================================================
   GENERATE PDF
   ===================================================== */

export async function generatePdfBlob(
  data,
  token
) {
  const response =
    await fetch(
      `${API_BASE_URL}/api/v1/generate-pdf`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json",

          ...(token
            ? {
                Authorization:
                  `Bearer ${token}`,
              }
            : {}),
        },

        body: JSON.stringify(data),
      }
    );


  if (!response.ok) {
    const result =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      result?.detail ||
        `PDF request failed (${response.status})`
    );
  }


  return response.blob();
}

/* =====================================================
   CAREER PROFILE
   ===================================================== */

export function getProfile(token) {
  return request("/api/v1/profile", {
    token,
  });
}


export function updateProfile({
  username,
  skills,
  targetRoles,
  experience,
  token,
}) {
  return request("/api/v1/profile", {
    method: "PUT",
    token,
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      skills,
      target_roles: targetRoles,
      experience,
    }),
  });
}


export function uploadProfileResume({
  file,
  token,
}) {
  const formData = new FormData();

  formData.append("resume", file);

  return request("/api/v1/profile/resume", {
    method: "POST",
    body: formData,
    token,
  });
}


export function completeOnboarding(token) {
  return request("/api/v1/profile/complete", {
    method: "POST",
    token,
  });
}
export async function transcribeInterviewAudio({
  audioBlob,
  token,
}) {
  const formData = new FormData();

  const extension =
    audioBlob.type?.includes("webm")
      ? "webm"
      : "wav";

  formData.append(
    "audio",
    audioBlob,
    `interview-answer.${extension}`
  );

  const response = await fetch(
    `${API_BASE_URL}/api/v1/speech/transcribe`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data?.detail ||
        "Speech transcription failed."
    );
  }

  return data;
}


export async function synthesizeInterviewSpeech({
  text,
  token,
  voice,
}) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/speech/synthesize`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        language: "en",
        voice: voice || null,
        format: "wav",
      }),
    }
  );

  if (!response.ok) {
    let message =
      "Speech synthesis failed.";

    try {
      const data = await response.json();

      message =
        data?.detail || message;
    } catch {
      // Keep default message.
    }

    throw new Error(message);
  }

  return response.blob();
}
/* =====================================================
   INTERVIEW — REPORT
   ===================================================== */

export function getInterviewReport({
  sessionId,
  token,
}) {
  return request(
    `/api/v1/interviews/${sessionId}/report`,
    {
      method: "GET",
      token,
    },
  );
}


/* =====================================================
   INTERVIEW — HISTORY
   ===================================================== */

export function getInterviewHistory({
  token,
}) {
  return request(
    `/api/v1/interviews/history`,
    {
      method: "GET",
      token,
    },
  );
}