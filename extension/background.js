importScripts("api.js");

const CE_TAB_URLS = [
  "https://chatgpt.com/*",
  "https://chat.openai.com/*",
  "https://www.google.com/search*",
  "https://google.com/search*",
];

function ceTabMatches(url) {
  if (!url) return false;
  return (
    url.startsWith("https://chatgpt.com/") ||
    url.startsWith("https://chat.openai.com/") ||
    url.includes("google.com/search")
  );
}

async function readStoredConfig() {
  return new Promise((resolve) => {
    try {
      chrome.storage.sync.get(
        { apiUrl: CE_DEFAULT_API, weights: CE_DEFAULT_WEIGHTS },
        (config) => resolve(config)
      );
    } catch {
      resolve({ apiUrl: CE_DEFAULT_API, weights: CE_DEFAULT_WEIGHTS });
    }
  });
}

async function syncConfigToTab(tabId, config) {
  const payload = JSON.stringify({
    apiUrl: ceNormalizeApiUrl(config.apiUrl || CE_DEFAULT_API),
    weights: config.weights || CE_DEFAULT_WEIGHTS,
  });

  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      func: (key, value) => localStorage.setItem(key, value),
      args: [CE_CONFIG_STORAGE_KEY, payload],
    });
  } catch {
    // Tab may not allow injection yet.
  }
}

async function syncConfigToOpenTabs(config) {
  const tabs = await chrome.tabs.query({ url: CE_TAB_URLS });
  for (const tab of tabs) {
    if (tab.id) await syncConfigToTab(tab.id, config);
  }
}

async function reloadOpenTabs() {
  const tabs = await chrome.tabs.query({ url: CE_TAB_URLS });
  for (const tab of tabs) {
    if (tab.id) {
      try {
        await chrome.tabs.reload(tab.id);
      } catch {
        // Tab may have closed.
      }
    }
  }
}

chrome.runtime.onInstalled.addListener(async (details) => {
  const config = await readStoredConfig();
  await syncConfigToOpenTabs(config);

  if (details.reason === "update") {
    await reloadOpenTabs();
    chrome.action.setBadgeText({ text: "" });
    chrome.action.setTitle({
      title: "CheckEverything — AI Trust Score",
    });
  }
});

chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete" || !ceTabMatches(tab.url)) return;
  const config = await readStoredConfig();
  await syncConfigToTab(tabId, config);
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "config_updated") {
    syncConfigToOpenTabs(message).finally(() => sendResponse({ ok: true }));
    return true;
  }

  if (message.type !== "review" && message.type !== "analyze") return;

  let responded = false;
  const reply = (payload) => {
    if (responded) return;
    responded = true;
    sendResponse(payload);
  };

  ceRunRequest(message)
    .then((result) => reply(result))
    .catch((err) => reply({ ok: false, error: err.message }));

  return true;
});
