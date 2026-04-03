// Capsolver content script — auto-solves Cloudflare Turnstile challenges
// Runs on every page, detects Turnstile iframes, and solves them via Capsolver API

(function () {
  let solved = false;

  function detectAndSolve() {
    if (solved) return;

    // Detect Cloudflare Turnstile widget
    const turnstileFrame = document.querySelector(
      'iframe[src*="challenges.cloudflare.com"]'
    );
    const turnstileDiv = document.querySelector(".cf-turnstile, [data-sitekey]");

    if (!turnstileFrame && !turnstileDiv) return;

    const siteKey =
      turnstileDiv?.getAttribute("data-sitekey") ||
      extractSiteKeyFromFrame(turnstileFrame);

    if (!siteKey) return;

    solved = true;
    console.log("[Capsolver] Turnstile detected, siteKey:", siteKey);

    chrome.runtime.sendMessage(
      {
        type: "solveTurnstile",
        url: window.location.href,
        siteKey: siteKey,
      },
      (response) => {
        if (response?.token) {
          console.log("[Capsolver] Turnstile solved");
          injectToken(response.token);
        } else {
          console.error("[Capsolver] Solve failed:", response?.error);
          solved = false; // allow retry
        }
      }
    );
  }

  function extractSiteKeyFromFrame(frame) {
    if (!frame) return null;
    try {
      const src = frame.getAttribute("src") || "";
      const match = src.match(/sitekey=([A-Za-z0-9_-]+)/);
      return match ? match[1] : null;
    } catch {
      return null;
    }
  }

  function injectToken(token) {
    // Find the hidden input that Turnstile uses and set the token
    const input = document.querySelector(
      '[name="cf-turnstile-response"], [name="g-recaptcha-response"]'
    );
    if (input) {
      input.value = token;
      // Trigger change event
      input.dispatchEvent(new Event("change", { bubbles: true }));
    }

    // Also try the Turnstile callback
    if (window.turnstile) {
      try {
        const widgets = document.querySelectorAll(".cf-turnstile");
        widgets.forEach((w) => {
          const cb = w.getAttribute("data-callback");
          if (cb && window[cb]) window[cb](token);
        });
      } catch (e) {
        console.error("[Capsolver] Callback injection failed:", e);
      }
    }

    // Submit form if present (Cloudflare challenge pages auto-submit)
    const form = document.querySelector("#challenge-form, form[action*='challenge']");
    if (form) {
      setTimeout(() => form.submit(), 500);
    }
  }

  // Watch for Turnstile appearing dynamically
  const observer = new MutationObserver(() => detectAndSolve());
  observer.observe(document.documentElement, { childList: true, subtree: true });

  // Also check immediately and on load
  detectAndSolve();
  window.addEventListener("DOMContentLoaded", detectAndSolve);
  window.addEventListener("load", detectAndSolve);
})();
