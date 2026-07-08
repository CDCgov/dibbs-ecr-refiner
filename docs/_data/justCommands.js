const path = require('path');
const { readJson } = require('./jsonUtils');

const justCommandsPath = path.join(__dirname, 'just-commands.json');

module.exports = function () {
  return readJson(justCommandsPath);
};
