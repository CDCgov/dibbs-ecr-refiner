const fs = require("fs");
const path = require("path");
const TOML = require("toml");

function readJson(filename) {
  const filePath = path.join(__dirname, filename);
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw);
}

function readToml(filename) {
  const filePath = path.join(__dirname, filename);
  const raw = fs.readFileSync(filePath, "utf-8");
  return TOML.parse(raw);
}

module.exports = { readJson, readToml };
