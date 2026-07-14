// Eleventy data file: reads glossary.toml and exports as a JS object.
const fs = require("fs");
const path = require("path");

module.exports = function () {
  const p = path.join(__dirname, "glossary.toml");
  if (!fs.existsSync(p)) {
    return { terms: [] };
  }

  const raw = fs.readFileSync(p, "utf-8");
  const terms = [];
  let current = null;
  let multilineKey = null;

  for (const line of raw.split("\n")) {
    const trimmed = line.trim();

    // Start a new term entry
    if (trimmed === "[[terms]]") {
      if (current && current.term) terms.push(current);
      current = {};
      multilineKey = null;
      continue;
    }

    if (!current) continue;

    // Check for multiline start: key = """
    const mlStart = trimmed.match(/^(\w+)\s*=\s*"""/);
    if (mlStart) {
      multilineKey = mlStart[1];
      current[multilineKey] = "";
      continue;
    }

    if (multilineKey) {
      if (trimmed === '"""') {
        current[multilineKey] = current[multilineKey].trim();
        multilineKey = null;
      } else {
        current[multilineKey] += (current[multilineKey] ? " " : "") + trimmed;
      }
      continue;
    }

    // Single-line value: key = "value"
    const single = trimmed.match(/^(\w+)\s*=\s*"(.*)"\s*$/);
    if (single) {
      current[single[1]] = single[2];
    }
  }

  if (current && current.term) terms.push(current);

  return { terms };
};
