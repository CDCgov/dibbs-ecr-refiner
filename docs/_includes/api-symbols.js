function flattenModules(data, mapSymbol) {
  const symbols = [];

  for (const module of data.modules || []) {
    for (const member of module.members || []) {
      symbols.push(mapSymbol(member, module));
    }
  }

  return symbols;
}

module.exports = { flattenModules };
