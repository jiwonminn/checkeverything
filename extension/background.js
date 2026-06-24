const DEFAULT_API = "http://localhost:8080";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type !== "review") return;

  chrome.storage.sync.get({ apiUrl: DEFAULT_API }, async (config) => {
    try {
      const res = await fetch(`${config.apiUrl}/api/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: message.code,
          language: message.language || "python",
          context: "ChatGPT AI code review — checkeverything extension",
          submission_type: "code",
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Review failed");
      sendResponse({ ok: true, data });
    } catch (err) {
      sendResponse({ ok: false, error: err.message });
    }
  });

  return true;
});
