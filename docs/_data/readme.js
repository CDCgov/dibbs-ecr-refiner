const fs = require("fs");
const path = require("path");

const readmePath = path.join(__dirname, "..", "..", "README.md");

module.exports = fs.readFileSync(readmePath, "utf-8");
