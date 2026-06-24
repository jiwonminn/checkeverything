// Intentionally vulnerable Express-style handler for demo reviews.

const express = require("express");
const app = express();

const API_KEY = "sk-live-abc123secret"; // hardcoded secret

app.get("/user", (req, res) => {
  const id = req.query.id;
  // SQL injection pattern (string concat)
  const query = "SELECT * FROM users WHERE id = " + id;
  db.query(query, (err, rows) => {
    res.json(rows);
  });
});

app.get("/fetch", async (req, res) => {
  const url = req.query.url;
  // SSRF: fetches arbitrary URL
  const response = await fetch(url);
  res.send(await response.text());
});

function parseConfig(input) {
  // Dangerous eval
  return eval("(" + input + ")");
}

function average(nums) {
  let sum = 0;
  for (let i = 0; i <= nums.length; i++) {
    sum += nums[i]; // off-by-one
  }
  return sum / nums.length;
}

module.exports = { app, parseConfig, average };
