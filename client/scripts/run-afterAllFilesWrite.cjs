const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

/**
 * Recursively finds all .ts files in a directory.
 * @param {string} dir
 * @param {string[]} fileList
 * @returns {string[]}
 */
function getTsFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  files.forEach((file) => {
    const filePath = path.join(dir, file);
    if (fs.statSync(filePath).isDirectory()) {
      getTsFiles(filePath, fileList);
    } else if (filePath.endsWith('.ts')) {
      fileList.push(filePath);
    }
  });
  return fileList;
}

/**
 * Removes trailing newlines from a file, ensuring exactly one remains.
 * @param {string} filePath
 */
function cleanTrailingNewlines(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');

  // Regex explanation:
  // \n{2,} matches 2 or more newline characters
  // $ matches the end of the string
  // We replace trailing newlines with a single newline
  const cleanedContent = content.replace(/\n{2,}$/, '\n');

  // Only write if content actually changed to avoid unnecessary disk I/O
  if (content !== cleanedContent) {
    // Ensure the file ends with at least one newline if it wasn't empty
    let finalContent = cleanedContent;
    if (finalContent.length > 0 && !finalContent.endsWith('\n')) {
      finalContent += '\n';
    }

    fs.writeFileSync(filePath, finalContent, 'utf8');
    console.log(`Cleaned: ${filePath}`);
  }
}

/**
 * Formats API files using Prettier and then cleans trailing newlines.
 */
async function runAfterAllFilesWrite() {
  const targetDir = './src/api';
  const absoluteTargetDir = path.resolve(process.cwd(), targetDir);

  if (!fs.existsSync(absoluteTargetDir)) {
    console.error(`Directory not found: ${absoluteTargetDir}`);
    process.exit(1);
  }

  try {
    console.log('Formatting API files with Prettier...');
    execSync('npx prettier --write ./src/api', { stdio: 'inherit' });

    console.log('Cleaning trailing newlines from API files...');
    const tsFiles = getTsFiles(absoluteTargetDir);
    tsFiles.forEach(cleanTrailingNewlines);
    console.log(`Processed ${tsFiles.length} files.`);

    console.log('API files formatted and cleaned successfully.');
  } catch (error) {
    console.error('Error occurred during post-write processing:');
    console.error(error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  runAfterAllFilesWrite();
}

module.exports = {
  getTsFiles,
  cleanTrailingNewlines,
  runAfterAllFilesWrite,
};
