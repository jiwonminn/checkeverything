const SAMPLE_SCENARIOS = [
  {
    context: "Demo: file download handler — path traversal risk",
    codes: {
      python: `from flask import Flask, request, send_file

app = Flask(__name__)
UPLOAD_DIR = "/var/app/uploads"

@app.route("/download")
def download():
    filename = request.args.get("file", "")
    path = UPLOAD_DIR + "/" + filename
    return send_file(path)
`,
      javascript: `const express = require("express");
const fs = require("fs");
const app = express();

app.get("/files", (req, res) => {
  const name = req.query.name;
  const filePath = "/data/uploads/" + name;
  res.send(fs.readFileSync(filePath));
});
`,
      typescript: `import express from "express";
import fs from "fs";

const app = express();

app.get("/files", (req, res) => {
  const name = req.query.name as string;
  const filePath = "/data/uploads/" + name;
  res.send(fs.readFileSync(filePath));
});
`,
      java: `import java.io.*;
import java.nio.file.*;

public class FileServlet {
    public byte[] readUserFile(String filename) throws IOException {
        Path path = Paths.get("/var/data", filename);
        return Files.readAllBytes(path);
    }
}
`,
      go: `package files

import (
    "net/http"
    "os"
    "path/filepath"
)

func DownloadHandler(w http.ResponseWriter, r *http.Request) {
    name := r.URL.Query().Get("file")
    path := filepath.Join("/var/data", name)
    data, _ := os.ReadFile(path)
    w.Write(data)
}
`,
      other: `UPLOAD_ROOT = "/var/uploads"

function download_file(name) {
  path = UPLOAD_ROOT + "/" + name
  return read_bytes(path)
}
`,
    },
  },
  {
    context: "Demo: dynamic code execution and reflected HTML",
    codes: {
      python: `import json

def run_plugin(user_code, payload):
    result = eval(user_code)
    return result

def render_bio(bio_html):
    return f"<section class='bio'>{bio_html}</section>"
`,
      javascript: `const express = require("express");
const app = express();

app.get("/run", (req, res) => {
  const code = req.query.code;
  const result = eval(code);
  res.send({ result });
});

app.post("/profile", (req, res) => {
  const bio = req.body.bio;
  res.send(\`<div class="bio">\${bio}</div>\`);
});
`,
      typescript: `import express from "express";

const app = express();

app.get("/sandbox", (req, res) => {
  const snippet = req.query.snippet as string;
  const output = eval(snippet);
  res.json({ output });
});

app.post("/preview", (req, res) => {
  const html = req.body.html as string;
  res.send(\`<article>\${html}</article>\`);
});
`,
      java: `public class PluginRunner {
    public Object execute(String userScript) {
        javax.script.ScriptEngine engine = new javax.script.ScriptEngineManager()
            .getEngineByName("javascript");
        try {
            return engine.eval(userScript);
        } catch (Exception e) {
            return null;
        }
    }
}
`,
      go: `package sandbox

import "os/exec"

func RunReport(name string) ([]byte, error) {
    cmd := exec.Command("sh", "-c", "render-report.sh "+name)
    return cmd.Output()
}
`,
      other: `function run_user_code(source) {
  return eval(source)
}

function render_page(body) {
  return "<main>" + body + "</main>"
}
`,
    },
  },
  {
    context: "Demo: token validation with weak hashing and secret logging",
    codes: {
      python: `import hashlib
import logging

API_TOKEN = "sk-live-abc123"

def validate_token(provided):
    logging.info(f"Checking token: {provided}")
    return hashlib.md5(provided.encode()).hexdigest() == hashlib.md5(API_TOKEN.encode()).hexdigest()
`,
      javascript: `const ADMIN_TOKEN = "admin-secret-token";

function checkAdminToken(input) {
  console.log("Validating token:", input);
  return input === ADMIN_TOKEN;
}
`,
      typescript: `const ADMIN_TOKEN = "admin-secret-token";

export function checkAdminToken(input: string): boolean {
  console.log("Validating:", input);
  if (input.length !== ADMIN_TOKEN.length) return false;
  let match = 0;
  for (let i = 0; i < input.length; i++) {
    match |= input.charCodeAt(i) ^ ADMIN_TOKEN.charCodeAt(i);
  }
  return match === 0;
}
`,
      java: `import java.security.MessageDigest;

public class PasswordStore {
    private static final String SALT = "mysalt";

    public static String hashPassword(String password) throws Exception {
        MessageDigest md = MessageDigest.getInstance("MD5");
        md.update((SALT + password).getBytes());
        return bytesToHex(md.digest());
    }
}
`,
      go: `package auth

import "crypto/md5"

const ServiceToken = "sk-live-go-token"

func ValidateToken(input string) bool {
    sum := md5.Sum([]byte(ServiceToken))
    provided := md5.Sum([]byte(input))
    return string(sum[:]) == string(provided[:])
}
`,
      other: `API_TOKEN = "sk-demo-key-12345"

function validate_token(value) {
  log("token check: " + value)
  return md5(value) == md5(API_TOKEN)
}
`,
    },
  },
  {
    context: "Demo: worker pool and unchecked index access",
    codes: {
      python: `cache = {}

def get_profile(user_id):
    return users[user_id]

def warm_cache(urls):
    for url in urls:
        for other in urls:
            cache[url] = fetch(other)
`,
      javascript: `let cache = null;

async function fetchConfig() {
  if (cache) return cache;
  const res = await fetch("https://api.example.com/config", {
    headers: { Authorization: "sk-live-xyz789" },
  });
  cache = await res.json();
  return cache;
}

function getUser(id) {
  return users[id];
}
`,
      typescript: `let cache: Record<string, unknown> | null = null;

export async function fetchConfig(): Promise<unknown> {
  if (cache) return cache;
  const res = await fetch("https://api.example.com/config", {
    headers: { Authorization: "sk-live-xyz789" },
  });
  cache = await res.json();
  return cache;
}
`,
      java: `public class WorkerPool {
    public void startMany() {
        for (int i = 0; i < 1000; i++) {
            new Thread(() -> {
                while (true) {
                    processNextJob();
                }
            }).start();
        }
    }
}
`,
      go: `package worker

func StartWorkers(jobs chan int, results chan int) {
    for i := 0; i < 1000; i++ {
        go func() {
            for job := range jobs {
                results <- job * 2
            }
        }()
    }
}

func Pick(items []string, index int) string {
    return items[index]
}
`,
      other: `cache = {}

function get_user(id) {
  return directory[id]
}

function warm_cache(items) {
  for a in items:
    for b in items:
      cache[a] = fetch(b)
}
`,
    },
  },
  {
    context: "Demo: small utility — mostly clean code",
    codes: {
      python: `"""Small math helpers."""

def clamp(value: float, low: float, high: float) -> float:
    """Return value constrained to the inclusive [low, high] range."""
    return max(low, min(high, value))

def average(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
`,
      javascript: `/** Clamp a number to an inclusive range. */
function clamp(value, low, high) {
  return Math.max(low, Math.min(high, value));
}

function average(values) {
  if (!values.length) return 0;
  return values.reduce((sum, n) => sum + n, 0) / values.length;
}
`,
      typescript: `/** Clamp a number to an inclusive range. */
export function clamp(value: number, low: number, high: number): number {
  return Math.max(low, Math.min(high, value));
}

export function average(values: number[]): number {
  if (!values.length) return 0;
  return values.reduce((sum, n) => sum + n, 0) / values.length;
}
`,
      java: `public final class MathUtils {
    private MathUtils() {}

    public static int clamp(int value, int low, int high) {
        return Math.max(low, Math.min(high, value));
    }

    public static double average(int[] values) {
        if (values.length == 0) return 0;
        int sum = 0;
        for (int value : values) sum += value;
        return (double) sum / values.length;
    }
}
`,
      go: `package mathx

func Clamp(value, low, high int) int {
    if value < low {
        return low
    }
    if value > high {
        return high
    }
    return value
}

func Average(values []float64) float64 {
    if len(values) == 0 {
        return 0
    }
    sum := 0.0
    for _, v := range values {
        sum += v
    }
    return sum / float64(len(values))
}
`,
      other: `function clamp(value, low, high) {
  if (value < low) return low
  if (value > high) return high
  return value
}
`,
    },
  },
  {
    context: "Demo: database auth helper — SQL injection and off-by-one",
    codes: {
      python: `import sqlite3

SECRET_KEY = "hardcoded-secret"

def login(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor.execute(query)
    return cursor.fetchone()

def process_items(items):
    total = 0
    for i in range(len(items) + 1):
        total += items[i]
    return total
`,
      javascript: `const SECRET_KEY = "hardcoded-secret";

function login(username, password) {
  const db = openDatabase("users.db");
  const query = \`SELECT * FROM users WHERE username = '\${username}' AND password = '\${password}'\`;
  return db.query(query);
}

function processItems(items) {
  let total = 0;
  for (let i = 0; i <= items.length; i++) {
    total += items[i];
  }
  return total;
}
`,
      typescript: `const SECRET_KEY = "hardcoded-secret";

interface User {
  id: number;
  username: string;
}

function login(username: string, password: string): User | null {
  const db = openDatabase("users.db");
  const query = \`SELECT * FROM users WHERE username = '\${username}' AND password = '\${password}'\`;
  return db.query<User>(query);
}

function processItems(items: number[]): number {
  let total = 0;
  for (let i = 0; i <= items.length; i++) {
    total += items[i];
  }
  return total;
}
`,
      java: `import java.sql.*;

public class AuthHelper {
    private static final String SECRET_KEY = "hardcoded-secret";

    public User login(String username, String password) throws SQLException {
        Connection conn = DriverManager.getConnection("jdbc:sqlite:users.db");
        String query = "SELECT * FROM users WHERE username = '" + username
            + "' AND password = '" + password + "'";
        Statement stmt = conn.createStatement();
        ResultSet rs = stmt.executeQuery(query);
        return rs.next() ? mapUser(rs) : null;
    }

    public int processItems(int[] items) {
        int total = 0;
        for (int i = 0; i <= items.length; i++) {
            total += items[i];
        }
        return total;
    }
}
`,
      go: `package auth

import (
    "database/sql"
    "fmt"
)

const SecretKey = "hardcoded-secret"

func Login(username, password string) (*User, error) {
    db, _ := sql.Open("sqlite3", "users.db")
    query := fmt.Sprintf(
        "SELECT * FROM users WHERE username = '%s' AND password = '%s'",
        username, password,
    )
    row := db.QueryRow(query)
    return scanUser(row)
}

func ProcessItems(items []int) int {
    total := 0
    for i := 0; i <= len(items); i++ {
        total += items[i]
    }
    return total
}
`,
      other: `SECRET_KEY = "hardcoded-secret"

function login(username, password) {
  query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
  return db.execute(query)
}

function process_items(items) {
  total = 0
  for i = 0; i <= len(items); i++ {
    total += items[i]
  }
  return total
}
`,
    },
  },
];

let sampleScenarioIndex = 0;

function nextCodeSample(language) {
  const scenario = SAMPLE_SCENARIOS[sampleScenarioIndex % SAMPLE_SCENARIOS.length];
  sampleScenarioIndex += 1;
  const code = scenario.codes[language] || scenario.codes.python;
  return { code, context: scenario.context };
}

const SAMPLE_DIFF = `diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,6 +1,10 @@
 import sqlite3
+SECRET_KEY = "hardcoded-secret"
 def login(username, password):
     conn = sqlite3.connect("users.db")
-    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
+    query = f"SELECT * FROM users WHERE username = '{username}'"
+    cursor.execute(query)
     return cursor.fetchone()
+def save_config(data):
+    exec(data)
`;

const SAMPLE_AI_TEXT = `Vitamin D supplements may reduce the risk of respiratory infections, according to several observational studies. Health authorities generally consider daily doses of 600–800 IU safe for most adults, though individual needs vary.

Some sources suggest higher doses (1,000–2,000 IU) for people with deficiency, but you should consult a healthcare provider before starting supplementation.`;

const SAMPLE_AI_URLS = `https://www.ncbi.nlm.nih.gov
https://www.who.int`;

const AGENTS = [
  "Security Agent",
  "Correctness Agent",
  "Readability Agent",
  "Performance Agent",
  "Test Coverage Agent",
];

const DEFAULT_REVIEW_WEIGHTS = {
  security: 20,
  correctness: 25,
  readability: 15,
  performance: 15,
  test_coverage: 25,
};

const DEFAULT_TRUST_WEIGHTS = {
  claim_support: 35,
  source_quality: 25,
  citation_accuracy: 25,
  freshness: 5,
  bias_context: 10,
};

const AGENT_WEIGHT_KEYS = {
  "Security Agent": "security",
  "Correctness Agent": "correctness",
  "Readability Agent": "readability",
  "Performance Agent": "performance",
  "Test Coverage Agent": "test_coverage",
};

const WEIGHT_FIELDS = [
  ["w-security", "security"],
  ["w-correctness", "correctness"],
  ["w-readability", "readability"],
  ["w-performance", "performance"],
  ["w-test_coverage", "test_coverage"],
];

const TRUST_WEIGHT_FIELDS = [
  ["tw-claim_support", "claim_support"],
  ["tw-source_quality", "source_quality"],
  ["tw-citation_accuracy", "citation_accuracy"],
  ["tw-freshness", "freshness"],
  ["tw-bias_context", "bias_context"],
];

const WEIGHTS_STORAGE_KEY = "checkeverything-review-weights";
const TRUST_WEIGHTS_STORAGE_KEY = "checkeverything-trust-weights";

let submissionMode = "code";
let reviewWeights = { ...DEFAULT_REVIEW_WEIGHTS };
let trustWeights = { ...DEFAULT_TRUST_WEIGHTS };
let appliedScoreWeights = null;

const codeEl = document.getElementById("code");
const diffEl = document.getElementById("diff");
const aiTextEl = document.getElementById("ai-text");
const aiUrlsEl = document.getElementById("ai-urls");
const languageEl = document.getElementById("language");
const contextEl = document.getElementById("context");
const contextRowEl = document.getElementById("context-row");
const weightsPanelEl = document.getElementById("weights-panel");
const trustWeightsPanelEl = document.getElementById("trust-weights-panel");
const weightTotalEl = document.getElementById("weight-total");
const trustWeightTotalEl = document.getElementById("trust-weight-total");
const resetWeightsBtn = document.getElementById("reset-weights");
const resetTrustWeightsBtn = document.getElementById("reset-trust-weights");
const submitBtn = document.getElementById("submit");
const loadSampleBtn = document.getElementById("load-sample");
const loadDiffSampleBtn = document.getElementById("load-diff-sample");
const loadTrustSampleBtn = document.getElementById("load-trust-sample");
const diffFileEl = document.getElementById("diff-file");
const diffSummaryEl = document.getElementById("diff-summary");
const errorEl = document.getElementById("error");
const introStateEl = document.getElementById("intro-state");
const resultsStateEl = document.getElementById("results-state");
const outputPanelEl = document.getElementById("output-panel");
const introStatusEl = document.getElementById("intro-status");
const introTrustStatusEl = document.getElementById("intro-trust-status");
const introCodeEl = document.getElementById("intro-code");
const introTrustEl = document.getElementById("intro-trust");
const resultsCodeViewEl = document.getElementById("results-code-view");
const resultsTrustViewEl = document.getElementById("results-trust-view");
const progressEl = document.getElementById("progress");
const charCountEl = document.getElementById("char-count");

const agentState = new Map(AGENTS.map((a) => [a, { status: "pending", report: null }]));

const CATEGORY_LABELS = {
  claim_support: "Claim Support",
  source_quality: "Source Quality",
  citation_accuracy: "Citation Accuracy",
  freshness: "Freshness",
  bias_context: "Bias / Context",
};

const SUPPORT_LABELS = {
  supported: "Supported",
  weakly_supported: "Weakly supported",
  not_supported: "Not supported",
  unclear: "Unclear",
  source_unavailable: "Source unavailable",
};

function readReviewWeights() {
  const weights = {};
  for (const [elementId, key] of WEIGHT_FIELDS) {
    weights[key] = Number(document.getElementById(elementId).value) || 0;
  }
  return weights;
}

function readTrustWeights() {
  const weights = {};
  for (const [elementId, key] of TRUST_WEIGHT_FIELDS) {
    weights[key] = Number(document.getElementById(elementId).value) || 0;
  }
  return weights;
}

function setReviewWeightInputs(weights) {
  for (const [elementId, key] of WEIGHT_FIELDS) {
    document.getElementById(elementId).value = weights[key];
  }
  updateWeightTotal();
}

function setTrustWeightInputs(weights) {
  for (const [elementId, key] of TRUST_WEIGHT_FIELDS) {
    document.getElementById(elementId).value = weights[key];
  }
  updateTrustWeightTotal();
}

function updateWeightTotal() {
  reviewWeights = readReviewWeights();
  const total = Object.values(reviewWeights).reduce((sum, value) => sum + value, 0);
  weightTotalEl.textContent = `${total}%`;
  weightTotalEl.classList.toggle("invalid", total !== 100);
  try {
    localStorage.setItem(WEIGHTS_STORAGE_KEY, JSON.stringify(reviewWeights));
  } catch {
    /* ignore storage errors */
  }
}

function updateTrustWeightTotal() {
  trustWeights = readTrustWeights();
  const total = Object.values(trustWeights).reduce((sum, value) => sum + value, 0);
  trustWeightTotalEl.textContent = `${total}%`;
  trustWeightTotalEl.classList.toggle("invalid", total !== 100);
  try {
    localStorage.setItem(TRUST_WEIGHTS_STORAGE_KEY, JSON.stringify(trustWeights));
  } catch {
    /* ignore storage errors */
  }
}

function loadStoredWeights() {
  try {
    const stored = localStorage.getItem(WEIGHTS_STORAGE_KEY);
    if (stored) {
      reviewWeights = { ...DEFAULT_REVIEW_WEIGHTS, ...JSON.parse(stored) };
      setReviewWeightInputs(reviewWeights);
      return;
    }
  } catch {
    /* ignore */
  }
  setReviewWeightInputs(DEFAULT_REVIEW_WEIGHTS);
}

function loadStoredTrustWeights() {
  try {
    const stored = localStorage.getItem(TRUST_WEIGHTS_STORAGE_KEY);
    if (stored) {
      trustWeights = { ...DEFAULT_TRUST_WEIGHTS, ...JSON.parse(stored) };
      setTrustWeightInputs(trustWeights);
      return;
    }
  } catch {
    /* ignore */
  }
  setTrustWeightInputs(DEFAULT_TRUST_WEIGHTS);
}

WEIGHT_FIELDS.forEach(([elementId]) => {
  document.getElementById(elementId).addEventListener("input", updateWeightTotal);
});

TRUST_WEIGHT_FIELDS.forEach(([elementId]) => {
  document.getElementById(elementId).addEventListener("input", updateTrustWeightTotal);
});

resetWeightsBtn.addEventListener("click", () => {
  setReviewWeightInputs(DEFAULT_REVIEW_WEIGHTS);
});

resetTrustWeightsBtn.addEventListener("click", () => {
  setTrustWeightInputs(DEFAULT_TRUST_WEIGHTS);
});

document.querySelectorAll(".sub-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    submissionMode = tab.dataset.mode;
    document.querySelectorAll(".sub-tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".mode-panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`mode-${submissionMode}`).classList.add("active");
    resetToIntroPanel();
    updateModeUI();
    updateCharCount();
    updateIntroState();
  });
});

loadSampleBtn.addEventListener("click", () => {
  submissionMode = "code";
  document.querySelector('[data-mode="code"]').click();
  const language = languageEl.value;
  const sample = nextCodeSample(language);
  codeEl.value = sample.code;
  contextEl.value = sample.context;
  updateCharCount();
  updateIntroState("sample");
});

loadDiffSampleBtn.addEventListener("click", () => {
  submissionMode = "diff";
  document.querySelector('[data-mode="diff"]').click();
  diffEl.value = SAMPLE_DIFF;
  parseDiffPreview();
  updateCharCount();
  updateIntroState("sample");
});

loadTrustSampleBtn.addEventListener("click", () => {
  submissionMode = "trust";
  document.querySelector('[data-mode="trust"]').click();
  aiTextEl.value = SAMPLE_AI_TEXT;
  aiUrlsEl.value = SAMPLE_AI_URLS;
  updateCharCount();
  updateIntroState("sample");
});

diffFileEl.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  diffEl.value = await file.text();
  submissionMode = "diff";
  document.querySelector('[data-mode="diff"]').click();
  parseDiffPreview();
  updateCharCount();
});

codeEl.addEventListener("input", () => {
  updateCharCount();
  updateIntroState("input");
});
diffEl.addEventListener("input", () => {
  updateCharCount();
  parseDiffPreview();
  updateIntroState("input");
});
aiTextEl.addEventListener("input", () => {
  updateCharCount();
  updateIntroState("input");
});

submitBtn.addEventListener("click", () => {
  if (submissionMode === "trust") runTrustAnalyze();
  else runReviewStream();
});

document.querySelectorAll("#results-code-view .tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#results-code-view .tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll("#results-code-view .tab-panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
  });
});

document.querySelectorAll("#results-trust-view .tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("#results-trust-view .tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll("#results-trust-view .tab-panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(`trust-tab-${tab.dataset.trustTab}`).classList.add("active");
  });
});

async function parseDiffPreview() {
  const diff = diffEl.value.trim();
  if (!diff) {
    diffSummaryEl.classList.add("hidden");
    return;
  }
  try {
    const res = await fetch("/api/parse-diff", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ diff }),
    });
    const data = await res.json();
    if (res.ok) {
      diffSummaryEl.textContent = data.context_note;
      diffSummaryEl.classList.remove("hidden");
      if (data.language) languageEl.value = data.language;
    }
  } catch {
    diffSummaryEl.classList.add("hidden");
  }
}

function buildPayload() {
  const base = {
    language: languageEl.value,
    context: contextEl.value.trim(),
    submission_type: submissionMode,
    weights: readReviewWeights(),
  };
  if (submissionMode === "diff") {
    return { ...base, diff: diffEl.value.trim(), code: "" };
  }
  return { ...base, code: codeEl.value.trim(), diff: "" };
}

function updateCharCount() {
  const n = submissionMode === "diff"
    ? diffEl.value.length
    : submissionMode === "trust"
      ? aiTextEl.value.length
      : codeEl.value.length;
  charCountEl.textContent = `${n.toLocaleString()} chars`;
  charCountEl.classList.toggle("warn", n > 40000);
}

function updateModeUI() {
  const isTrust = submissionMode === "trust";
  contextRowEl.classList.toggle("hidden", isTrust);
  weightsPanelEl.classList.toggle("hidden", isTrust);
  trustWeightsPanelEl.classList.toggle("hidden", !isTrust);
  introCodeEl.classList.toggle("hidden", isTrust);
  introTrustEl.classList.toggle("hidden", !isTrust);
  if (!submitBtn.disabled) {
    submitBtn.querySelector(".btn-text").textContent = isTrust
      ? "Check Trust Score"
      : "Run 5-Agent Review";
  }
}

function showResultsView(mode) {
  const isTrust = mode === "trust";
  resultsCodeViewEl.classList.toggle("hidden", isTrust);
  resultsTrustViewEl.classList.toggle("hidden", !isTrust);
}

function showResultsPanel() {
  introStateEl.classList.add("hidden");
  resultsStateEl.classList.remove("hidden");
  outputPanelEl?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function resetToIntroPanel() {
  introStateEl.classList.remove("hidden");
  resultsStateEl.classList.add("hidden");
}

function activateCodeResultsTab(tabName) {
  document.querySelectorAll("#results-code-view .tab").forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.tab === tabName);
  });
  document.querySelectorAll("#results-code-view .tab-panel").forEach((panel) => {
    panel.classList.remove("active");
  });
  document.getElementById(`tab-${tabName}`)?.classList.add("active");
}

function processStreamChunk(buffer) {
  const events = [];
  const parts = buffer.split("\n\n");
  const remainder = parts.pop() || "";
  for (const chunk of parts) {
    const line = chunk.trim();
    if (!line.startsWith("data: ")) continue;
    events.push(JSON.parse(line.slice(6)));
  }
  return { events, remainder };
}

function updateIntroState(trigger) {
  if (introStateEl.classList.contains("hidden")) return;

  if (submissionMode === "trust") {
    const hasContent = aiTextEl.value.trim().length > 0;
    if (trigger === "sample" || hasContent) {
      introTrustStatusEl.textContent = "Sample loaded — ready to check.";
      document.getElementById("trust-step-load").classList.add("step-done");
      document.getElementById("trust-step-run").classList.add("step-next");
    } else {
      introTrustStatusEl.textContent = "Paste an AI answer on the left to check its claims.";
      document.getElementById("trust-step-load").classList.remove("step-done");
      document.getElementById("trust-step-run").classList.remove("step-next");
    }
    return;
  }

  const hasContent = submissionMode === "diff"
    ? diffEl.value.trim().length > 0
    : codeEl.value.trim().length > 0;

  if (trigger === "sample" || hasContent) {
    introStatusEl.textContent = "Sample loaded — ready to run.";
    document.getElementById("step-load").classList.add("step-done");
    document.getElementById("step-run").classList.add("step-next");
  } else {
    introStatusEl.textContent = "Paste code or a PR diff on the left to get started.";
    document.getElementById("step-load").classList.remove("step-done");
    document.getElementById("step-run").classList.remove("step-next");
  }
}

function formatApiError(detail, status) {
  if (status === 404) {
    return "API not found — restart the server with ./scripts/dev.sh and hard-refresh.";
  }
  if (!detail) return "Request failed";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || item.message || String(item)).join("; ");
  }
  return String(detail);
}

async function runTrustAnalyze() {
  const text = aiTextEl.value.trim();
  const urls = aiUrlsEl.value.split("\n").map((u) => u.trim()).filter(Boolean);

  if (!text) {
    showError("Please paste an AI-generated answer to analyze.");
    return;
  }

  setLoading(true);
  hideError();
  showResultsPanel();
  showResultsView("trust");
  showProgress("Checking sources and claims…");
  clearTrustResults();

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, urls, source: "other", weights: readTrustWeights() }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(formatApiError(data.detail, res.status));
    renderTrustResults(data);
    document.getElementById("trust-step-see")?.classList.add("step-done");
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
    hideProgress();
  }
}

async function runReviewStream() {
  const payload = buildPayload();
  if (submissionMode === "code" && !payload.code) {
    showError("Please paste some code to review.");
    return;
  }
  if (submissionMode === "diff" && !payload.diff) {
    showError("Please paste or upload a PR diff.");
    return;
  }

  resetAgentState();
  setLoading(true);
  hideError();
  showResultsPanel();
  showResultsView("code");
  activateCodeResultsTab("findings");
  showProgress("Initializing agents…");
  renderAgentGrid();
  clearResults();

  try {
    const res = await fetch("/api/review/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(formatApiError(err.detail, res.status));
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (value) {
        buffer += decoder.decode(value, { stream: true });
        const parsed = processStreamChunk(buffer);
        buffer = parsed.remainder;
        for (const event of parsed.events) {
          handleStreamEvent(event);
        }
      }
      if (done) break;
    }

    const trailing = buffer.trim();
    if (trailing.startsWith("data: ")) {
      handleStreamEvent(JSON.parse(trailing.slice(6)));
    }
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
    hideProgress();
  }
}

function handleStreamEvent(event) {
  switch (event.type) {
    case "status":
      setProgressMessage(event.message);
      break;
    case "agent_start":
      agentState.set(event.agent, { status: "running", report: null });
      renderAgentGrid();
      setProgressMessage(`${event.agent} analyzing…`);
      break;
    case "agent_complete":
      agentState.set(event.report.agent_name, { status: "done", report: event.report });
      renderAgentGrid();
      appendFindingsForAgent(event.report);
      break;
    case "coordinator_start":
      setProgressMessage(event.message || "Coordinator synthesizing…");
      break;
    case "fallback":
      setProgressMessage(event.message);
      break;
    case "complete":
      renderResults(event.data);
      document.getElementById("step-see")?.classList.add("step-done");
      break;
    case "error":
      showError(event.message);
      break;
  }
}

function resetAgentState() {
  AGENTS.forEach((a) => agentState.set(a, { status: "pending", report: null }));
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  const isTrust = submissionMode === "trust";
  submitBtn.querySelector(".btn-text").textContent = loading
    ? (isTrust ? "Analyzing response…" : "5 agents analyzing…")
    : (isTrust ? "Check Trust Score" : "Run 5-Agent Review");
  submitBtn.querySelector(".btn-spinner").classList.toggle("hidden", !loading);
}

function showProgress(msg) {
  progressEl.classList.remove("hidden");
  progressEl.innerHTML = `<div class="progress-msg">${escapeHtml(msg)}</div>`;
}

function hideProgress() {
  progressEl.classList.add("hidden");
}

function setProgressMessage(msg) {
  progressEl.innerHTML = `<div class="progress-msg">${escapeHtml(msg)}</div>`;
}

function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove("hidden");
}

function hideError() {
  errorEl.classList.add("hidden");
}

function clearTrustResults() {
  document.getElementById("trust-overall-score").textContent = "—";
  document.getElementById("trust-headline").textContent = "Analyzing claims and sources…";
  document.getElementById("trust-summary").textContent = "";
  const sourceSummary = document.getElementById("trust-source-summary");
  sourceSummary.innerHTML = "";
  sourceSummary.classList.add("hidden");
  document.getElementById("category-grid").innerHTML = "";
  document.getElementById("claims-list").innerHTML = "";
  document.getElementById("sources-list").innerHTML = "";
  document.querySelector("#trust-json-output code").textContent = "";
}

function renderTrustResults(data) {
  document.getElementById("trust-overall-score").textContent = data.overall_score;
  document.getElementById("trust-headline").textContent = data.headline || "";
  document.getElementById("trust-summary").textContent = data.support_summary || "";
  renderTrustSourceSummary(data.source_summary);

  document.getElementById("category-grid").innerHTML = Object.entries(CATEGORY_LABELS)
    .map(([key, label]) => {
      const cat = data.categories?.[key];
      if (!cat) return "";
      const weight = trustWeights[key] ?? DEFAULT_TRUST_WEIGHTS[key];
      return `
        <div class="category-card">
          <h3>${escapeHtml(label)} <span class="category-weight">${weight}%</span></h3>
          <div class="category-score">${cat.score}</div>
          <p>${escapeHtml(cat.summary || "")}</p>
        </div>`;
    })
    .join("");

  document.getElementById("claims-list").innerHTML = (data.claims || []).length
    ? (data.claims || []).map((claim) => {
        const support = SUPPORT_LABELS[claim.support_label] || claim.status?.replace(/_/g, " ") || "—";
        const supportClass = claim.support_label || "unclear";
        return `
          <li class="claim-card support-${supportClass}">
            <div class="claim-header">
              <span class="support-badge">${escapeHtml(support)}</span>
              ${claim.confidence_level ? `<span class="confidence-badge">${escapeHtml(claim.confidence_level)} confidence</span>` : ""}
            </div>
            <p class="claim-text">${escapeHtml(claim.text)}</p>
            ${claim.matched_source ? `<p class="claim-source"><strong>Source:</strong> ${escapeHtml(claim.matched_source)}</p>` : ""}
            ${claim.evidence_note || claim.note ? `<p class="claim-note">${escapeHtml(claim.evidence_note || claim.note)}</p>` : ""}
            ${claim.confidence_note ? `<p class="claim-note">${escapeHtml(claim.confidence_note)}</p>` : ""}
            ${claim.citations?.length ? `<div class="claim-citations">${claim.citations.map((url) => `<a href="${escapeHtml(url)}" target="_blank" rel="noopener">${escapeHtml(formatCitationLabel(url))}</a>`).join("")}</div>` : ""}
          </li>`;
      }).join("")
    : '<li class="claim-card"><p class="claim-text">No individual claims extracted.</p></li>';

  const sources = data.sources || [];
  document.getElementById("sources-list").innerHTML = sources.length
    ? sources.map((src) => `
        <li class="source-card ${src.reachable ? "reachable" : "unreachable"}">
          <div class="source-header">
            <strong>${escapeHtml(src.domain)}</strong>
            <span class="source-quality">${escapeHtml(src.source_quality)}</span>
          </div>
          <a class="source-url" href="${escapeHtml(src.url)}" target="_blank" rel="noopener">${escapeHtml(src.url)}</a>
          <p>${escapeHtml(src.notes || src.title || "")}</p>
        </li>`).join("")
    : '<li class="source-card"><p>No cited URLs provided or detected.</p></li>';

  document.querySelector("#trust-json-output code").textContent = JSON.stringify(data, null, 2);
}

function renderTrustSourceSummary(summary) {
  const el = document.getElementById("trust-source-summary");
  if (!summary) {
    el.innerHTML = "";
    el.classList.add("hidden");
    return;
  }
  const issues = summary.issues || [];
  el.innerHTML = `
    <div>
      <strong>${summary.reachable_count}/${summary.sources_checked}</strong>
      sources reachable
    </div>
    <div>
      <strong>${summary.primary_official_count}</strong>
      primary or official
    </div>
    ${issues.length ? `<ul>${issues.map((issue) => `<li>${escapeHtml(issue)}</li>`).join("")}</ul>` : ""}
  `;
  el.classList.remove("hidden");
}

function formatCitationLabel(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function clearResults() {
  appliedScoreWeights = null;
  document.getElementById("overall-score").textContent = "—";
  document.getElementById("verdict-badge").textContent = "—";
  document.getElementById("executive-summary").textContent = "Waiting for coordinator…";
  const strengthsEl = document.getElementById("strengths-list");
  strengthsEl.innerHTML = "";
  strengthsEl.classList.add("hidden");
  document.getElementById("findings-list").innerHTML = "";
  document.getElementById("action-list").innerHTML = "";
  document.getElementById("markdown-report").innerHTML = "";
  document.getElementById("meta-bar").classList.add("hidden");
}

function getAgentWeightPercent(agentName) {
  const key = AGENT_WEIGHT_KEYS[agentName];
  if (!key) return null;
  if (appliedScoreWeights?.[key] != null) return appliedScoreWeights[key];
  return reviewWeights[key] ?? null;
}

function renderAgentGrid() {
  document.getElementById("agent-grid").innerHTML = AGENTS.map((name) => {
    const state = agentState.get(name) || { status: "pending" };
    const score = state.report?.score ?? "—";
    const count = state.report?.findings?.length ?? "—";
    const weight = getAgentWeightPercent(name);
    return `
      <div class="agent-card status-${state.status}">
        <div class="agent-status-icon">${statusIcon(state.status)}</div>
        <div class="agent-card-header">
          <h3>${escapeHtml(shortName(name))}</h3>
          ${weight != null ? `<span class="agent-weight">${weight}%</span>` : ""}
        </div>
        <div class="agent-score">${score}</div>
        <div class="finding-count">${count === "—" ? "pending" : `${count} finding(s)`}</div>
      </div>`;
  }).join("");
}

function shortName(name) {
  return name.replace(" Agent", "");
}

function statusIcon(status) {
  if (status === "done") return "✓";
  if (status === "running") return "◌";
  return "·";
}

function appendFindingsForAgent(report) {
  if (!report.findings?.length) return;
  const list = document.getElementById("findings-list");
  const section = document.createElement("section");
  section.className = "findings-agent-section";
  section.innerHTML = `
    <h3 class="findings-agent-title">${escapeHtml(report.agent_name)}
      <span class="score-pill">${report.score}/100</span></h3>
    <p class="findings-summary">${escapeHtml(report.summary)}</p>
    ${(report.findings || []).map((f) => `
      <article class="finding-card severity-${f.severity}">
        <div class="finding-header">
          <span class="severity-badge">${escapeHtml(f.severity)}</span>
          <strong>${escapeHtml(f.title)}</strong>
        </div>
        ${f.line_hint ? `<div class="line-hint">📍 ${escapeHtml(f.line_hint)}</div>` : ""}
        <p>${escapeHtml(f.description)}</p>
        <div class="recommendation"><strong>Fix:</strong> ${escapeHtml(f.recommendation)}</div>
      </article>`).join("")}
  `;
  list.appendChild(section);
}

function renderResults(wrapper) {
  const data = wrapper.report || wrapper;
  const meta = wrapper.report ? wrapper : null;
  appliedScoreWeights = meta?.score_weights || wrapper.score_weights || null;

  document.getElementById("overall-score").textContent = data.overall_score;
  const badge = document.getElementById("verdict-badge");
  badge.textContent = formatVerdict(data.verdict);
  badge.className = `verdict-badge verdict-${data.verdict}`;
  document.getElementById("executive-summary").textContent = data.executive_summary;

  const strengthsEl = document.getElementById("strengths-list");
  const strengths = data.strengths || [];
  if (strengths.length) {
    strengthsEl.innerHTML = strengths.map((s) => `<li>${escapeHtml(s)}</li>`).join("");
    strengthsEl.classList.remove("hidden");
  } else {
    strengthsEl.innerHTML = "";
    strengthsEl.classList.add("hidden");
  }

  if (meta) {
    document.getElementById("meta-bar").classList.remove("hidden");
    const weightsNote = appliedScoreWeights
      ? ` · Weights: Sec ${appliedScoreWeights.security}%`
      : "";
    document.getElementById("pipeline-badge").textContent =
      `Pipeline: ${meta.pipeline.toUpperCase()} · ${meta.google_technologies.join(" + ")}${weightsNote}`;
    document.getElementById("duration-badge").textContent =
      `${meta.model} · ${meta.duration_ms}ms`;
  }

  (data.agent_reports || []).forEach((r) => {
    agentState.set(r.agent_name, { status: "done", report: r });
  });
  renderAgentGrid();

  const findingsList = document.getElementById("findings-list");
  findingsList.innerHTML = "";
  (data.agent_reports || []).forEach(appendFindingsForAgent);
  if (!findingsList.children.length) {
    findingsList.innerHTML = '<p class="findings-empty">No significant issues were flagged in this submission.</p>';
  }

  document.getElementById("markdown-report").innerHTML = renderMarkdown(data.markdown_report || "");
  document.getElementById("action-list").innerHTML = (data.action_items || []).map((item) => `
    <li class="action-item">
      <div class="priority priority-${item.priority}">${formatPriority(item.priority)}</div>
      <div class="category">${escapeHtml(item.category)}</div>
      <div class="action-text">${escapeHtml(item.action)}</div>
      <div class="rationale">${escapeHtml(item.rationale)}</div>
    </li>`).join("");
  document.querySelector("#json-output code").textContent = JSON.stringify(meta || data, null, 2);
}

function formatVerdict(v) {
  return { approve: "Approve", request_changes: "Request Changes", reject: "Reject" }[v] || v;
}

function formatPriority(p) {
  return { must_fix: "Must Fix", should_fix: "Should Fix", nice_to_have: "Nice to Have" }[p] || p;
}

function escapeHtml(str) {
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function renderMarkdown(md) {
  return escapeHtml(md)
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>\n?)+/g, (m) => `<ul>${m}</ul>`)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n\n/g, "</p><p>")
    .replace(/^(?!<[hul])/gm, (line) => (line.trim() ? `<p>${line}</p>` : ""))
    .replace(/<p><\/p>/g, "");
}

updateCharCount();
loadStoredWeights();
loadStoredTrustWeights();
updateModeUI();
updateIntroState();
