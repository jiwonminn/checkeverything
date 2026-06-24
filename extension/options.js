const DEFAULT_API = "http://localhost:8080";
const DEFAULT_WEIGHTS = {
  claim_support: 35,
  source_quality: 25,
  citation_accuracy: 25,
  bias_context: 10,
  freshness: 5,
};

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

document.getElementById("save").addEventListener("click", () => {
  const apiUrl = document.getElementById("apiUrl").value.trim() || DEFAULT_API;
  const weights = readWeights();
  chrome.storage.sync.set({ apiUrl, weights }, () => {
    document.getElementById("status").textContent = "Saved!";
  });
});

WEIGHT_FIELDS.forEach(([elementId]) => {
  const input = document.getElementById(elementId);
  if (input) input.addEventListener("input", updateWeightTotal);
});

chrome.storage.sync.get({ apiUrl: DEFAULT_API, weights: DEFAULT_WEIGHTS }, (data) => {
  document.getElementById("apiUrl").value = data.apiUrl;
  setWeights(data.weights || DEFAULT_WEIGHTS);
});
