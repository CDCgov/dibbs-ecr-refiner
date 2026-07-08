const path = require('path');
const { readJson } = require('./jsonUtils');

const pyPath = path.join(__dirname, 'python-api.json');

function slugify(value) {
  return String(value)
    .toLowerCase()
    .replace(/\./g, '/')
    .replace(/[^a-z0-9/]+/g, '-')
    .replace(/(^-|-$)+/g, '');
}

module.exports = function () {
  const pyData = readJson(pyPath);

  const modules = (pyData.modules || []).map(module => ({
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
