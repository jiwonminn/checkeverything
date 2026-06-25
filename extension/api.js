/* Shared API client for CheckEverything extension (content script + service worker). */

// API presets — pick one in Extension options (Local dev vs Cloud Run).
const CE_CLOUD_API = "https://checkeverything-jgaheeinfq-pd.a.run.app";
const CE_LOCAL_DEV_API = "http://localhost:8080";
const CE_DEFAULT_API = CE_CLOUD_API;
const CE_CONFIG_VERSION = 3;
const CE_CONFIG_STORAGE_KEY = "checkeverything_config";
const CE_REQUEST_TIMEOUT_MS = 150_000;
const CE_DEFAULT_WEIGHTS = {
  claim_support: 35,
  source_quality: 25,
  citation_accuracy: 25,
  bias_context: 10,
  freshness: 5,
};

function ceNormalizeApiUrl(apiUrl) {
  return String(apiUrl || CE_DEFAULT_API).trim().replace(/\/+$/, "");
}

function ceReadCachedConfig() {
  try {
    const raw = localStorage.getItem(CE_CONFIG_STORAGE_KEY);
    if (!raw) {
      return { apiUrl: CE_DEFAULT_API, weights: { ...CE_DEFAULT_WEIGHTS } };
    }
    const parsed = JSON.parse(raw);
    return {
      apiUrl: ceNormalizeApiUrl(parsed.apiUrl || CE_DEFAULT_API),
      weights: parsed.weights || { ...CE_DEFAULT_WEIGHTS },
    };
  } catch {
    return { apiUrl: CE_DEFAULT_API, weights: { ...CE_DEFAULT_WEIGHTS } };
  }
}

function ceWriteCachedConfig(config) {
  try {
    localStorage.setItem(
      CE_CONFIG_STORAGE_KEY,
      JSON.stringify({
        apiUrl: ceNormalizeApiUrl(config.apiUrl || CE_DEFAULT_API),
        weights: config.weights || { ...CE_DEFAULT_WEIGHTS },
        configVersion: CE_CONFIG_VERSION,
      })
    );
  } catch {
    // Ignore quota / blocked storage on some pages.
  }
}

function ceEnsureCachedConfig() {
  if (!ceHasPageStorage()) return;
  if (localStorage.getItem(CE_CONFIG_STORAGE_KEY)) return;
  ceWriteCachedConfig({ apiUrl: CE_DEFAULT_API, weights: { ...CE_DEFAULT_WEIGHTS } });
}

function ceHasPageStorage() {
  try {
    return typeof localStorage !== "undefined";
  } catch {
    return false;
  }
}

function formatBadgeError(message) {
  const text = String(message || "Analysis failed");
  if (text.includes("Cannot reach API")) return "API unreachable — check Extension options";
  if (text.includes("timed out")) return "Timed out — try again";
  return text.length > 48 ? `${text.slice(0, 45)}…` : text;
}

function ceGetExtensionConfig() {
  // Content scripts must never call chrome.storage (it uses runtime.sendMessage).
  if (ceHasPageStorage()) {
    ceEnsureCachedConfig();
    return Promise.resolve(ceReadCachedConfig());
  }

  return new Promise((resolve) => {
    try {
      chrome.storage.sync.get(
        { apiUrl: CE_DEFAULT_API, weights: CE_DEFAULT_WEIGHTS },
        (config) => {
          if (chrome.runtime?.lastError) {
            resolve({ apiUrl: CE_DEFAULT_API, weights: { ...CE_DEFAULT_WEIGHTS } });
            return;
          }
          resolve(config);
        }
      );
    } catch {
      resolve({ apiUrl: CE_DEFAULT_API, weights: { ...CE_DEFAULT_WEIGHTS } });
    }
  });
}

async function cePostJson(apiUrl, path, body) {
  const baseUrl = ceNormalizeApiUrl(apiUrl);
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), CE_REQUEST_TIMEOUT_MS);

  let res;
  try {
    res = await fetch(`${baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (err) {
    if (err?.name === "AbortError") {
      throw new Error(
        `Analysis timed out after ${CE_REQUEST_TIMEOUT_MS / 1000}s. Check Extension options → API URL (${baseUrl}).`
      );
    }
    throw new Error(
      `Cannot reach API at ${baseUrl}. Open Extension options and set your API URL (Cloud Run or ${CE_LOCAL_DEV_API} for local dev).`
    );
  } finally {
    clearTimeout(timeoutId);
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "Request failed";
    throw new Error(detail);
  }
  return data;
}

async function ceRunRequest(message) {
  const config = await ceGetExtensionConfig();
  const apiUrl = config.apiUrl || CE_DEFAULT_API;
  const weights = config.weights || CE_DEFAULT_WEIGHTS;

  if (message.type === "analyze") {
    const data = await cePostJson(apiUrl, "/api/analyze", {
      text: message.text,
      urls: message.urls || [],
      source: message.source || "chatgpt",
      weights,
    });
    return {
      ok: true,
      data: { mode: "trust", platform: message.source || "chatgpt", ...data },
    };
  }

  if (message.type === "review") {
    const data = await cePostJson(apiUrl, "/api/review", {
      code: message.code,
      language: message.language || "python",
      context: "ChatGPT AI code review — CheckEverything extension",
      submission_type: "code",
    });
    return {
      ok: true,
      data: { mode: "code", report: data.report, pipeline: data.pipeline },
    };
  }

  throw new Error(`Unknown request type: ${message.type}`);
}
