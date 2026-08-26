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
  files.forEach(file => {
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

function main() {
  const apiDir = path.join(process.cwd(), 'client', 'src', 'api');

  if (!fs.existsSync(apiDir)) {
    console.error(`Directory not found: ${apiDir}`);
    process.exit(1);
  }

  try {
    const tsFiles = getTsFiles(apiDir);
    tsFiles.forEach(cleanTrailingNewlines);
    console.log(`Processed ${tsFiles.length} files.`);
  } catch (err) {
    console.error(`Error processing files: ${err.message}`);
    process.exit(1);
  }
}

main();
