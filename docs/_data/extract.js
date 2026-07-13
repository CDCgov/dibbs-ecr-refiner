// Extraction is now handled by:
// - Initial sync: `just docs::serve` runs `sync` before starting
// - Live updates: watch.py monitors Python files and re-extracts on change
//
// This data file no longer triggers extraction to avoid rebuild loops.

module.exports = function () {
  return {};
};
