const path = require('path');
const { readJson } = require('./jsonUtils');

const tsPath = path.join(__dirname, 'typescript-api.json');

function slugify(value) {
  return String(value)
    .toLowerCase()
    .replace(/\./g, '/')
    .replace(/[^a-z0-9/]+/g, '-')
    .replace(/(^-|-$)+/g, '');
}

module.exports = function () {
  const tsData = readJson(tsPath);

  const modules = (tsData.modules || []).map(module => ({
    ...module,
    slug: slugify(module.name),
    memberCount: (module.members || []).length,
    members: (module.members || []).map(member => ({
      ...member,
      description: member.docstring || '',
    })),
  }));

  return { modules };
};
