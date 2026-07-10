const { execSync } = require("child_process");
const path = require("path");

// Track last extraction time to avoid re-extracting on every rebuild
let lastExtraction = 0;
const EXTRACT_INTERVAL = 2000; // minimum ms between extractions

function extractIfNeeded() {
  const now = Date.now();
  if (now - lastExtraction < EXTRACT_INTERVAL) return;
  lastExtraction = now;

  try {
    execSync("just docs::sync", { cwd: path.join(__dirname, ".."), stdio: "pipe" });
  } catch (e) {
    // Silently fail — extraction errors are shown by the Python scripts
  }
}

module.exports = function () {
  extractIfNeeded();
  return {};
};
