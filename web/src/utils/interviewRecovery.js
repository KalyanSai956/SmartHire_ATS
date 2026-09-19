const STORAGE_PREFIX = "smarthire:interview:";

function getKey(sessionId) {
  return `${STORAGE_PREFIX}${sessionId}`;
}

export function saveInterviewDraft(
  sessionId,
  data,
) {
  if (!sessionId) {
    return;
  }

  try {
    localStorage.setItem(
      getKey(sessionId),
      JSON.stringify({
        ...data,
        savedAt: Date.now(),
      }),
    );
  } catch (error) {
    console.warn(
      "[Interview Recovery] Could not save draft:",
      error,
    );
  }
}

export function loadInterviewDraft(sessionId) {
  if (!sessionId) {
    return null;
  }

  try {
    const raw = localStorage.getItem(
      getKey(sessionId),
    );

    if (!raw) {
      return null;
    }

    return JSON.parse(raw);
  } catch (error) {
    console.warn(
      "[Interview Recovery] Could not load draft:",
      error,
    );

    return null;
  }
}

export function clearInterviewDraft(sessionId) {
  if (!sessionId) {
    return;
  }

  try {
    localStorage.removeItem(
      getKey(sessionId),
    );
  } catch (error) {
    console.warn(
      "[Interview Recovery] Could not clear draft:",
      error,
    );
  }
}