const fs = require("fs");
const path = require("path");

/**
 * Helper to read a file and provide a clear error if it is missing.
 * @param {string} relativePath Path relative to docs/_data/
 * @returns {string} File content
 */
function readReadme(relativePath) {
  try {
    const fullPath = path.join(__dirname, "..", "..", relativePath);
    if (!fs.existsSync(fullPath)) {
      throw new Error(`File not found: ${fullPath}`);
    }
    return fs.readFileSync(fullPath, "utf-8");
  } catch (error) {
    return `Error loading README at ${relativePath}: ${error.message}`;
  }
}

module.exports = {
  main: readReadme("README.md"),

  keycloak: readReadme("keycloak/README.md"),

  designReview: readReadme("design-review/README.MD"),

  refiner: {
    root: readReadme("refiner/README.md"),
    app: readReadme("refiner/app/README.md"),
    api: readReadme("refiner/app/api/README.md"),
    core: readReadme("refiner/app/core/README.md"),
    db: readReadme("refiner/app/db/README.md"),
    lambda: readReadme("refiner/app/lambda/README.md"),
    services: readReadme("refiner/app/services/README.md"),
    ecr: readReadme("refiner/app/services/ecr/README.md"),
    narrative: readReadme("refiner/app/services/ecr/narrative/README.md"),
    migrations: readReadme("refiner/migrations/README.md"),
    scripts: readReadme("refiner/scripts/README.md"),
    data: readReadme("refiner/scripts/data/README.md"),
    jurisdictionPackages: readReadme("refiner/scripts/data/jurisdiction-packages/README.md"),
    oidCatalogBuilder: readReadme("refiner/scripts/oid_catalog_builder/README.md"),
    tes: readReadme("refiner/tes/README.md"),
  },

  client: {
    root: readReadme("client/README.md"),
    dropdown: readReadme("client/src/components/Dropdown/README.md"),
    e2e: readReadme("client/e2e/README.md"),
  },

  testing: {
    integrationScenarios: readReadme("refiner/tests/integration/scenarios/README.md"),
    validation: readReadme("refiner/tests/validation/README.md"),
  },

  api: {
    dataModel: readReadme("docs/refiner/data-model/README.md"),
    tes: readReadme("docs/tes/README.md"),
  },

  ops: readReadme("ops/README.md"),

  config: readReadme("docs/README.md"),
};
