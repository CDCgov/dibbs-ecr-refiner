const { readJson } = require("./jsonUtils");

module.exports = function () {
  return readJson("lambda-api.json");
};
