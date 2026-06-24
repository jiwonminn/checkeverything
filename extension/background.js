const DEFAULT_API = "http://localhost:8080";
const DEFAULT_WEIGHTS = {
  claim_support: 35,
  source_quality: 25,
  citation_accuracy: 25,
  bias_context: 10,
  freshness: 5,
};

async function postJson(apiUrl, path, body) {
  const res = await fetch(`${apiUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "Request failed";
    throw new Error(detail);
  }
  return data;
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type !== "review" && message.type !== "analyze") return;

  chrome.storage.sync.get({ apiUrl: DEFAULT_API, weights: DEFAULT_WEIGHTS }, async (config) => {
    try {
      if (message.type === "analyze") {
        const data = await postJson(config.apiUrl, "/api/analyze", {
          text: message.text,
          urls: message.urls || [],
          source: message.source || "chatgpt",
          weights: config.weights || DEFAULT_WEIGHTS,
        });
        sendResponse({
          ok: true,
          data: { mode: "trust", platform: message.source || "chatgpt", ...data },
        });
        return;
      }

      const data = await postJson(config.apiUrl, "/api/review", {
        code: message.code,
        language: message.language || "python",
        context: "ChatGPT AI code review — CheckEverything extension",
        submission_type: "code",
      });
      sendResponse({
        ok: true,
        data: { mode: "code", report: data.report, pipeline: data.pipeline },
      });
    } catch (err) {
      sendResponse({ ok: false, error: err.message });
    }
  });

  return true;
});
