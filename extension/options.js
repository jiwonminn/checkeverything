const DEFAULT_WEIGHTS = CE_DEFAULT_WEIGHTS;

const WEIGHT_FIELDS = [
  ["w_claim_support", "claim_support"],
  ["w_source_quality", "source_quality"],
  ["w_citation_accuracy", "citation_accuracy"],
  ["w_bias_context", "bias_context"],
  ["w_freshness", "freshness"],
];

function readWeights() {
  const weights = {};
  for (const [elementId, key] of WEIGHT_FIELDS) {
    const input = document.getElementById(elementId);
    weights[key] = input ? Number(input.value) || 0 : DEFAULT_WEIGHTS[key];
  }
  return weights;
}

function updateWeightTotal() {
  const weights = readWeights();
  const total = Object.values(weights).reduce((sum, value) => sum + value, 0);
  const totalEl = document.getElementById("weightTotal");
  if (!totalEl) return;
  totalEl.textContent = `Total: ${total}%`;
  totalEl.classList.toggle("invalid", total !== 100);
}

function setWeights(weights) {
  for (const [elementId, key] of WEIGHT_FIELDS) {
    const input = document.getElementById(elementId);
    if (input) input.value = weights[key];
  }
  updateWeightTotal();
}

function updatePresetButtons() {
  const apiUrl = ceNormalizeApiUrl(document.getElementById("apiUrl").value.trim() || CE_DEFAULT_API);
  const localBtn = document.getElementById("presetLocal");
  const cloudBtn = document.getElementById("presetCloud");
  const isLocal = apiUrl.startsWith(CE_LOCAL_DEV_API) || apiUrl.startsWith("http://127.0.0.1:8080");
  const isCloud = apiUrl === ceNormalizeApiUrl(CE_CLOUD_API);
  localBtn.classList.toggle("active", isLocal);
  cloudBtn.classList.toggle("active", isCloud);
}

async function testApiConnection(apiUrl) {
  const baseUrl = ceNormalizeApiUrl(apiUrl);
  const res = await fetch(`${baseUrl}/health`, { method: "GET" });
  if (!res.ok) throw new Error(`Health check failed (${res.status})`);
  return res.json();
}

function saveConfig(apiUrl) {
  const weights = readWeights();
  const config = { apiUrl: ceNormalizeApiUrl(apiUrl), weights };
  chrome.storage.sync.set(config, () => {
    document.getElementById("status").textContent = "Saved!";
    document.getElementById("status").style.color = "#34a853";
    chrome.runtime.sendMessage({ type: "config_updated", ...config });
    updatePresetButtons();
  });
}

document.getElementById("presetLocal").addEventListener("click", () => {
  document.getElementById("apiUrl").value = CE_LOCAL_DEV_API;
  updatePresetButtons();
});

document.getElementById("presetCloud").addEventListener("click", () => {
  document.getElementById("apiUrl").value = CE_CLOUD_API;
  updatePresetButtons();
});

document.getElementById("openLocalDemo").addEventListener("click", (event) => {
  event.preventDefault();
  chrome.tabs.create({ url: `${CE_LOCAL_DEV_API}/demo/chatgpt` });
});

document.getElementById("apiUrl").addEventListener("input", updatePresetButtons);

document.getElementById("save").addEventListener("click", () => {
  const apiUrl = document.getElementById("apiUrl").value.trim() || CE_DEFAULT_API;
  saveConfig(apiUrl);
});

document.getElementById("test").addEventListener("click", async () => {
  const status = document.getElementById("status");
  const apiUrl = document.getElementById("apiUrl").value.trim() || CE_DEFAULT_API;
  status.textContent = "Testing…";
  status.style.color = "#5f6368";
  try {
    const health = await testApiConnection(apiUrl);
    status.textContent = `Connected (${health.service || "ok"})`;
    status.style.color = "#34a853";
  } catch (err) {
    status.textContent = err.message || "Connection failed";
    status.style.color = "#d93025";
  }
});

WEIGHT_FIELDS.forEach(([elementId]) => {
  const input = document.getElementById(elementId);
  if (input) input.addEventListener("input", updateWeightTotal);
});

chrome.storage.sync.get({ apiUrl: CE_DEFAULT_API, weights: DEFAULT_WEIGHTS }, (data) => {
  document.getElementById("apiUrl").value = data.apiUrl || CE_DEFAULT_API;
  setWeights(data.weights || DEFAULT_WEIGHTS);
  updatePresetButtons();
});
