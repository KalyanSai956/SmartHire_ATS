const sleep = (ms) =>
  new Promise((resolve) => setTimeout(resolve, ms));

function isRetryableError(error) {
  const message = String(error?.message || "").toLowerCase();

  return (
    message.includes("failed to fetch") ||
    message.includes("network") ||
    message.includes("timeout") ||
    message.includes("503") ||
    message.includes("502") ||
    message.includes("504")
  );
}

export async function retryRequest(
  operation,
  {
    retries = 3,
    baseDelay = 700,
    shouldRetry = isRetryableError,
  } = {},
) {
  let lastError;

  for (let attempt = 0; attempt <= retries; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;

      if (
        attempt >= retries ||
        !shouldRetry(error)
      ) {
        throw error;
      }

      const delay =
        baseDelay * Math.pow(2, attempt);

      await sleep(delay);
    }
  }

  throw lastError;
}