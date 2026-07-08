const { EleventyHtmlBasePlugin, EleventyRenderPlugin } = require("@11ty/eleventy");

module.exports = function (eleventyConfig) {
  eleventyConfig.addPlugin(EleventyHtmlBasePlugin, {
    base: "/docs",
  });

  eleventyConfig.addPassthroughCopy({ "css": "css" });

  // Watch generated docs data so `docs::serve` refreshes when sync rewrites it.
  eleventyConfig.addWatchTarget("./_data/**/*.json");
  eleventyConfig.addWatchTarget("./_data/**/*.js");

  // Use Eleventy's Render plugin so templates can render markdown/liquid
  // content consistently via the `render` filter.
  eleventyConfig.addPlugin(EleventyRenderPlugin);

  // Basic HTML sanitizer filter to remove dangerous elements and attributes.
  // Note: this is intentionally conservative but not a full sanitizer
  // library. If you need stricter guarantees, consider adding a vetted
  // dependency like `sanitize-html` and using that instead.
  eleventyConfig.addFilter("sanitize", (value) => {
    if (!value) return "";
    let s = String(value);
    // remove script and style blocks
    s = s.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "");
    s = s.replace(/<style[\s\S]*?>[\s\S]*?<\/style>/gi, "");
    // remove iframes, objects, embeds, meta, link
    s = s.replace(/<(iframe|object|embed|link|meta)[\s\S]*?>[\s\S]*?<\/\1>/gi, "");
    s = s.replace(/<(iframe|object|embed|link|meta)[\s\S]*?>/gi, "");
    // strip event handler attributes like onload=, onclick= etc.
    s = s.replace(/\son\w+\s*=\s*("[\s\S]*?"|'[\s\S]*?'|[^\s>]+)/gi, "");
    // strip style attributes
    s = s.replace(/\sstyle\s*=\s*("[\s\S]*?"|'[\s\S]*?'|[^\s>]+)/gi, "");
    // neutralize javascript: URIs in href/src
    s = s.replace(/(href|src)\s*=\s*("|')\s*javascript:[\s\S]*?\2/gi, '$1=$2#$2');
    return s;
  });

  return {
    dir: {
      input: ".",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
    pathPrefix: "",
    markdownTemplateEngine: false,
    htmlTemplateEngine: "liquid",
    dataTemplateEngine: "liquid",
    ignores: [
      "risk-assessments/**",
      "2025-12-16-stage-gate-508-scan-results/**",
      "diagrams/**",
      "refiner/**",
      "tes/**",
      "node_modules/**",
      "_site/**",

    ],
  };
};
