// Capsolver extension background service worker
// Receives API key from environment and provides it to content script

const CAPSOLVER_API_KEY = "CAPSOLVER_API_KEY_PLACEHOLDER";

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "getApiKey") {
    sendResponse({ apiKey: CAPSOLVER_API_KEY });
  }
  if (msg.type === "solveTurnstile") {
    fetch("https://api.capsolver.com/createTask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clientKey: CAPSOLVER_API_KEY,
        task: {
          type: "AntiTurnstileTaskProxyLess",
          websiteURL: msg.url,
          websiteKey: msg.siteKey,
        },
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.taskId) {
          pollResult(data.taskId, sendResponse);
        } else {
          sendResponse({ error: data.errorDescription || "Task creation failed" });
        }
      })
      .catch((e) => sendResponse({ error: e.message }));
    return true; // async response
  }
});

function pollResult(taskId, sendResponse, attempts = 0) {
  if (attempts > 30) {
    sendResponse({ error: "Timeout waiting for solution" });
    return;
  }
  setTimeout(() => {
    fetch("https://api.capsolver.com/getTaskResult", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clientKey: "CAPSOLVER_API_KEY_PLACEHOLDER", taskId }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.status === "ready") {
          sendResponse({ token: data.solution?.token });
        } else {
          pollResult(taskId, sendResponse, attempts + 1);
        }
      })
      .catch((e) => sendResponse({ error: e.message }));
  }, 2000);
}
