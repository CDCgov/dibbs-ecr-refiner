alias h := _default
alias help := _default

@_default:
    just --list --list-submodules

[group('alias')]
[doc('Alias for `client`')]
mod c './.justscripts/just/client.just'

[group('alias')]
[doc('Alias for `database`')]
mod db './.justscripts/just/database.just'

[group('alias')]
[doc('Alias for `decisions`')]
mod rfc './.justscripts/just/decisions.just'

[group('alias')]
[doc('Alias for `migrate`')]
mod m './.justscripts/just/migrate.just'

[group('alias')]
[doc('Alias for `server`')]
mod s './.justscripts/just/server.just'

[group('alias')]
[doc('Alias for `cloud`')]
mod cd './.justscripts/just/cloud.just'

[group('alias')]
[doc('Alias for `dev`')]
mod d './.justscripts/just/dev.just'

[group('alias')]
[doc('Alias for `structurizr`')]
mod s9r './.justscripts/just/structurizr.just'

[group('sub-command')]
[doc('Run commands against `client/` code')]
mod client './.justscripts/just/client.just'

[group('sub-command')]
[doc('Run dev-related docker compose commands')]
mod dev './.justscripts/just/dev.just'

[group('sub-command')]
[doc('Run database commands against `refiner/` code')]
mod database './.justscripts/just/database.just'

[group('sub-command')]
[doc('Run migration commands')]
mod migrate './.justscripts/just/migrate.just'

[group('sub-command')]
[doc('Run server commands against `refiner/` code')]
mod server './.justscripts/just/server.just'

[group('sub-command')]
[doc('Run commands against Azure')]
mod cloud './.justscripts/just/cloud.just'

[group('sub-command')]
[doc('Run Structurizr commands')]
mod structurizr './.justscripts/just/structurizr.just'

[group('sub-command')]
[doc('Run decision records commands')]
mod decisions './.justscripts/just/decisions.just'

alias l := lint
alias t := test

[doc('Run linting and formatting rules on all code')]
lint:
    just client::run lint fmt
    just server::lint

[group('test')]
[doc('Run tests on all code')]
test:
    just server::test
    just client::run test:coverage
    just client::run e2e

# NOTE: The recipe below named `_new` is **only** called from other Justfiles
# that create files from .template files found next to them. Currently it's
# used for managing and authoring `docs/decisions`.

[private]
_new title type folder:
    #!/usr/bin/env node
    const fs = require('node:fs');
    const path = require('node:path');

    const today = new Date().toISOString().split('T')[0];
    const title = "{{ title }}";
    const fileTitle = "{{ kebabcase(title) }}";

    console.info(`📝 Creating a new {{ type }} on ${today}`);

    console.info(`🔍 Found {{ type }} title: ${title}`);

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

    console.info(`🔦 Checking for existing {{ type }}s in ${fullWritePath}`);

    const resolvedPath = path.resolve(fullWritePath);

    const template = fs.readFileSync(`${fullWritePath}/.template`)

    const files = fs.readdirSync(resolvedPath)
      .map(fileName => {
        return path.join(fullWritePath, fileName);
      })
      .filter(isFile);

    console.info(`🔍 Found ${(files.length + "").padStart(4, '0')} {{ type }}(s)`);

    const nextNumber = files.length + 1;
    const nextNumberString = (nextNumber + "").padStart(4, '0');

    console.info(`🖊️ Setting your new {{ type }} to #${nextNumberString}`);

    const nextFilePath = path.join(
        resolvedPath,
        `${nextNumberString}_${today}_${fileTitle}.md`
    );

    console.info(`📊 Attempting to save {{ type }} #${nextNumberString} to ${nextFilePath}`);

    const content = eval(`\`${template}\``);

    try {
      fs.writeFileSync(nextFilePath, content);
      console.log(`✅ Successfully created {{ type }} #${nextNumberString} for ${title} at ${nextFilePath}`);
    } catch (e) {
      console.error(`❌ ${e}`);
    }
