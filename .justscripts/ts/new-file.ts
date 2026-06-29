import fs from "node:fs";
import path from "node:path";
import os from "node:os";

/**
 * NOTE: These variables are injected globally by the Just tool
 * via the `read()` function before the script is executed.
 */
declare const JUST_TITLE: string;
declare const JUST_TITLE_SAFE: string;
declare const JUST_TYPE: string;
declare const JUST_RUN_DIR: string;
declare const JUST_FOLDER: string;

const today = new Date().toISOString().split("T")[0];
const title = JUST_TITLE;
const fileTitle = JUST_TITLE_SAFE;
const isCve = JUST_TYPE === "risk assessment";

console.info(`📝 Creating a new ${JUST_TYPE} on ${today}`);
console.info(`🔍 Found ${JUST_TYPE} title: ${title}`);

const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "new-"));
const runningFromDir = path.join(JUST_RUN_DIR);
const folderPath = JUST_FOLDER;

// Determine the base directory for writing the file
let fullWritePath: string;
if (runningFromDir.endsWith(folderPath)) {
  fullWritePath = runningFromDir;
} else {
  fullWritePath = path.join(runningFromDir, folderPath);
}

/**
 * Check if a path is a file and contains a 4-digit sequence.
 * PERF: Using .test() is more efficient than .match() for boolean checks.
 */
const isFile = (fileName: string): boolean => {
  const re = /[0-9]{4}/;
  try {
    return fs.lstatSync(fileName).isFile() && re.test(fileName);
  } catch {
    return false;
  }
};

let resolvedPath = "";
let nextNumberString = "";

if (isCve) {
  console.info(
    `🕵️ This is a ${JUST_TYPE} and will be saved to a temporary directory`,
  );
} else {
  console.info(`🔦 Checking for existing ${JUST_TYPE}s in ${fullWritePath}`);
  resolvedPath = path.resolve(fullWritePath);

  const files = fs
    .readdirSync(resolvedPath)
    .map((fileName: string) => path.join(fullWritePath, fileName))
    .filter(isFile);

  console.info(
    `🔍 Found ${(files.length + "").padStart(4, "0")} ${JUST_TYPE}(s)`,
  );

  // Calculate the next index for the filename
  const nextNumber = files.length + 1;
  nextNumberString = nextNumber.toString().padStart(4, "0");

  console.info(`🖊️ Setting your new ${JUST_TYPE} to #${nextNumberString}`);
}

const nextFilePath = path.join(
  isCve ? tmpDir : resolvedPath,
  isCve
    ? `${today}_${fileTitle}.md`
    : `${nextNumberString}_${today}_${fileTitle}.md`,
);

if (isCve) {
  console.info(`📊 Attempting to save ${JUST_TYPE} to ${nextFilePath}`);
} else {
  console.info(
    `📊 Attempting to save ${JUST_TYPE} #${nextNumberString} to ${nextFilePath}`,
  );
}

/**
 * NOTE: Removed eval() to mitigate RCE risks.
 * We use a replacement map to interpolate template variables safely.
 */
const template = fs.readFileSync(`${fullWritePath}/.template`, "utf8");
const replacements: Record<string, string> = {
  JUST_TITLE: title,
  JUST_TYPE: JUST_TYPE,
  today: today,
};

const content = template.replace(/\${(\w+)}/g, (_, key) => {
  return replacements[key] || `\${${key}}`;
});

try {
  fs.writeFileSync(nextFilePath, content);
  const successMsg = isCve
    ? `✅ Successfully created ${JUST_TYPE} for ${title} at ${nextFilePath}`
    : `✅ Successfully created ${JUST_TYPE} #${nextNumberString} for ${title} at ${nextFilePath}`;
  console.log(successMsg);
} catch (e) {
  console.error(`❌ ${e}`);
}

/**
 * TODO: Move the interpolation logic to a utility function if
 * other Just scripts need similar template capabilities.
 */
