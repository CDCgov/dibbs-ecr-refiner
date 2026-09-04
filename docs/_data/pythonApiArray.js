const { readJson } = require("./jsonUtils");

module.exports = function () {
  return readJson("python-api.json");
};
