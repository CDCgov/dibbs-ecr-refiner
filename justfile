alias h := _default
alias help := _default

@_default:
    just --list --list-submodules

# Alias for `docker`
[group: 'alias']
mod dk './.justscripts/just/docker.just'

# Alias for `client`
[group: 'alias']
mod c './.justscripts/just/client.just'

# Alias for `database`
[group: 'alias']
mod db './.justscripts/just/database.just'

# Alias for `risk-assessments`
[group: 'alias']
mod cve './.justscripts/just/risk-assessments.just'

# Alias for `decisions`
[group: 'alias']
mod rfc './.justscripts/just/decisions.just'

# Alias for `migrate`
[group: 'alias']
mod m './.justscripts/just/migrate.just'

# Alias for `server`
[group: 'alias']
mod s './.justscripts/just/server.just'

# Alias for `cloud`
[group: 'alias']
mod cd './.justscripts/just/cloud.just'

# Alias for `dev`
[group: 'alias']
mod d './.justscripts/just/dev.just'

# Run `docs` commands
[group: 'sub-command']
mod docs './.justscripts/just/docs.just'

# Run docker build commands
[group: 'sub-command']
mod docker './.justscripts/just/docker.just'

# Run commands against `client/` code
[group: 'sub-command']
mod client './.justscripts/just/client.just'

# Run dev-related docker compose commands
[group: 'sub-command']
mod dev './.justscripts/just/dev.just'

# Run database commands against `refiner/` code
[group: 'sub-command']
mod database './.justscripts/just/database.just'

# Run migration commands
[group: 'sub-command']
mod migrate './.justscripts/just/migrate.just'

# Run server commands against `refiner/` code
[group: 'sub-command']
mod server './.justscripts/just/server.just'

# Run commands against Azure
[group: 'sub-command']
mod cloud './.justscripts/just/cloud.just'

# Run risk assessments commands
[group: 'sub-command']
mod risk-assessments './.justscripts/just/risk-assessments.just'

# Run decision records commands
[group: 'sub-command']
mod decisions './.justscripts/just/decisions.just'

alias l := lint
alias t := test

[doc('Run linting and formatting rules on all code')]
lint:
    just client::run lint fmt
    just server::lint

[doc('Run tests on all code')]
[group('test')]
test:
    just server::test
    just client::run test:coverage
    just client::run e2e

# NOTE: The recipe below named `_new` is **only** called from other Justfiles
# that create files from .template files found next to them. Currently it's
# used for managing and authoring `docs/decisions` and `docs/risk-assessments`

[private]
_new title type folder:
    #!/usr/bin/env node
    const fs = require('node:fs');
    const path = require('node:path');
    const os = require('os');

    const today = new Date().toISOString().split('T')[0];
    const title = "{{ title }}";
    const fileTitle = "{{ kebabcase(title) }}";
    const isCve = "{{ type }}" === "risk assessment"

    console.info(`📝 Creating a new {{ type }} on ${today}`);

    console.info(`🔍 Found {{ type }} title: ${title}`);

    const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'new-'));
    const runningFromDir = path.join("{{ replace(justfile_directory(), '\', '/') }}");
    const folderPath = '{{ folder }}';

    let fullWritePath;
    if (runningFromDir.endsWith(folderPath)) {
      fullWritePath = runningFromDir;
    } else {
      fullWritePath = path.join(runningFromDir, folderPath);
    }

    const isFile = fileName => {
      const re = /[0-9]{4}/g;
      return fs.lstatSync(fileName).isFile() && fileName.match(re);
    };
    let resolvedPath = ''
    let nextNumberString = ''
    let nextNumber = ''

    if (isCve) {
      console.info(`🕵️ This is a {{ type }} and will be saved to a temporary directory`)
    } else {
      console.info(`🔦 Checking for existing {{ type }}s in ${fullWritePath}`);
      resolvedPath = path.resolve(fullWritePath);


      const files = fs.readdirSync(resolvedPath)
        .map(fileName => {
          return path.join(fullWritePath, fileName);
          })
        .filter(isFile);

      console.info(`🔍 Found ${(files.length + "").padStart(4, '0')} {{ type }}(s)`);

      nextNumber = files.length + 1;
      nextNumberString = (nextNumber + "").padStart(4, '0');


      console.info(`🖊️ Setting your new {{ type }} to #${nextNumberString}`);
    }

    const nextFilePath = path.join(
        (isCve ? tmpDir : resolvedPath),
        (isCve ? `${today}_${fileTitle}.md` : `${nextNumberString}_${today}_${fileTitle}.md`)
    );

    if (isCve) {
      console.info(`📊 Attempting to save {{ type }} to ${nextFilePath}`)
    } else {
      console.info(`📊 Attempting to save {{ type }} #${nextNumberString} to ${nextFilePath}`);
    }

    const template = fs.readFileSync(`${fullWritePath}/.template`)
    const content = eval(`\`${template}\``);

    try {
      fs.writeFileSync(nextFilePath, content);
      if (isCve) {
        console.log(`✅ Successfully created {{ type }} for ${title} at ${nextFilePath}`);
      } else {
        console.log(`✅ Successfully created {{ type }} #${nextNumberString} for ${title} at ${nextFilePath}`);
      }
    } catch (e) {
      console.error(`❌ ${e}`);
    }
