/*   _______                          __
 *  |    ___|.--.--.-----.-----.----.|  |_
 *  |    ___||_   _|  _  |  _  |   _||   _|
 *  |_______||__.__|   __|_____|__|  |____|
 *                 |__|
 *   _____  __
 *  |     \|__|.---.-.-----.----.---.-.--------.-----.
 *  |  --  |  ||  _  |  _  |   _|  _  |        |__ --|
 *  |_____/|__||___._|___  |__| |___._|__|__|__|_____|
 *                   |_____|
 *
 * NOTE: The purpose of this script is to use Puppeteer to export Structurizr
 * Lite diagrams from the browser renderer. This provides the highest fidelity
 * diagrams.
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const FILENAME_SUFFIX = '';

const PNG_FORMAT = 'png';
const SVG_FORMAT = 'svg';

const IGNORE_HTTPS_ERRORS = true;
const HEADLESS = true;

const IMAGE_VIEW_TYPE = 'Image';

// if (process.argv.length < 4 && process.env['CI']) {
//   console.log('Usage: <structurizrUrl> <png|svg> [username] [password]');
//   process.exit(1);
// }

const url = process.argv[2] || 'http://localhost:9001/workspace/diagrams';
const format = process.argv[3] || 'png';

if (format !== PNG_FORMAT && format !== SVG_FORMAT) {
  console.error(`Supported output format is either ${PNG_FORMAT} or ${SVG_FORMAT}. You provided ${format}.`);
  process.exit(1);
}

var expectedNumberOfExports = 0;
var actualNumberOfExports = 0;

(async () => {
  const browser = await puppeteer.launch({
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
    ],
    ignoreHTTPSErrors: IGNORE_HTTPS_ERRORS,
    executablePath: process.env.PUPPETEER_EXEC_PATH,
    headless: HEADLESS,
  });
  const page = await browser.newPage();


  console.info(' _  _  _  _ . _  _ ');
  console.info(`(_)|_)(/_| ||| |(_|: ${url}`);
  console.info('   |             _|');
  console.info('');

  // Visit the diagrams page
  await page.goto(url, {
    waitUntil: 'domcontentloaded',
  });

  await page.waitForFunction(
    'structurizr.scripting && structurizr.scripting.isDiagramRendered() === true'
  );

  if (format === PNG_FORMAT) {
    // Add function to the page to save the generated PNG images
    await page.exposeFunction('savePNG', (content, filename) => {

      console.info('   |`.| _  _  _  _ _  _ ');
      console.info(`  ~|~||(/_| |(_|| | |(/_: ${filename}`);
      console.info('');

      content = content.replace(/^data:image\/png;base64,/, "");
      fs.writeFile(path.join("rendered", filename), content, 'base64', function (err) {
        if (err) throw err;
      });

      actualNumberOfExports++;

      if (actualNumberOfExports === expectedNumberOfExports) {

        console.info(' |`. _ . _|_  _  _|');
        console.info('~|~|| ||_\\| |(/_(_|');

        browser.close();
      }
    });
  }

  // Gather the array of views
  const views = await page.evaluate(() => {
    return structurizr.scripting.getViews();
  });

  views.forEach(function (view) {
    if (view.type === IMAGE_VIEW_TYPE) {
      expectedNumberOfExports++; // diagrams only
    } else {
      expectedNumberOfExports++; // diagram
      expectedNumberOfExports++; // key
    }
  });

  console.info('(~_|_ _  __|_. _  _ ');
  console.info('_) | (_||  | || |(_|');
  console.info('                  _|');
  console.info(' _    _  _  __|_');
  console.info(`(/_><|_)(_)|  | : ${format}`);
  console.info('     |          ');
  console.info('');

  if (!fs.existsSync("rendered")) {
    fs.mkdirSync("rendered", { recursive: true });
  }

  for (let idx = 0; idx < views.length; idx++) {
    const view = views[idx];

    await page.evaluate((view) => {
      structurizr.scripting.changeView(view.key);
    }, view);

    await page.waitForFunction(
      'structurizr.scripting.isDiagramRendered() === true'
    );

    if (format === SVG_FORMAT) {
      const diagramFilename = `${FILENAME_SUFFIX}${view.key}.svg`;
      const diagramKeyFilename = `${FILENAME_SUFFIX}${view.key}-key.svg`;

      let svgForDiagram = await page.evaluate(() => {
        return structurizr.scripting.exportCurrentDiagramToSVG({
          includeMetadata: true,
        });
      });

      console.info('   |`.| _  _  _  _ _  _ ');
      console.info(`  ~|~||(/_| |(_|| | |(/_: ${diagramFilename}`);
      console.info('');

      fs.writeFile(path.join("rendered", diagramFilename), svgForDiagram, function (err) {
        if (err) throw err;
      });
      actualNumberOfExports++;

      if (view.type !== IMAGE_VIEW_TYPE) {
        let svgForKey = await page.evaluate(() => {
          return structurizr.scripting.exportCurrentDiagramKeyToSVG();
        });

        console.info('   |`.| _  _  _  _ _  _ ');
        console.info(`  ~|~||(/_| |(_|| | |(/_: ${diagramKeyFilename}`);
        console.info('');

        fs.writeFile(path.join("rendered", diagramKeyFilename), svgForKey, function (err) {
          if (err) throw err;
        });
        actualNumberOfExports++;
      }

      if (actualNumberOfExports === expectedNumberOfExports) {

        console.info(' |`. _ . _|_  _  _|');
        console.info('~|~|| ||_\\| |(/_(_|');
        console.info('');

        browser.close();
      }
    } else {
      const diagramFilename = `${FILENAME_SUFFIX}${view.key}.png`;
      const diagramKeyFilename = `${FILENAME_SUFFIX}${view.key}-key.png`;

      console.info('   |`.| _  _  _  _ _  _ ');
      console.info(`  ~|~||(/_| |(_|| | |(/_: ${diagramFilename}`);
      console.info('');

      page.evaluate((diagramFilename) => {
        structurizr.scripting.exportCurrentDiagramToPNG({
          includeMetadata: true,
          crop: false,
        }, function (png) {
          window.savePNG(png, diagramFilename);
        })
      }, diagramFilename);

      if (view.type !== IMAGE_VIEW_TYPE) {

        console.info('   |`.| _  _  _  _ _  _ ');
        console.info(`  ~|~||(/_| |(_|| | |(/_: ${diagramKeyFilename}`);
        console.info('');

        page.evaluate((diagramKeyFilename) => {
          structurizr.scripting.exportCurrentDiagramKeyToPNG(function (png) {
            window.savePNG(png, diagramKeyFilename);
          });
        }, diagramKeyFilename);
      }
    }
  }
})();
