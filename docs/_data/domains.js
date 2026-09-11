const TOML = require("toml");
const fs = require("fs");
const path = require("path");

module.exports = function () {
  const filePath = path.join(__dirname, "..", "_includes", "domains.toml");
  const raw = fs.readFileSync(filePath, "utf-8");
  return TOML.parse(raw).domains || [];
};
