const { EleventyRenderPlugin } = require("@11ty/eleventy");
const markdownIt = require("markdown-it");
const sanitize = require("sanitize-html");
const md = new markdownIt({ html: true, breaks: false, linkify: false });

module.exports = function(eleventyConfig) {
  eleventyConfig.addPassthroughCopy({ "css": "css" });
  eleventyConfig.addPassthroughCopy({ "img": "img" });

  // Watch generated docs data so `docs::serve` refreshes when sync rewrites it.
  // Note: Python source watching is handled by watch.py which re-extracts on change
  eleventyConfig.addWatchTarget("./_data/**/*.json");
  eleventyConfig.addWatchTarget("./_data/**/*.toml");

  // Use Eleventy's Render plugin so templates can render markdown/liquid
  // content consistently via the `render` filter.
  eleventyConfig.addPlugin(EleventyRenderPlugin);

  // Render markdown strings to HTML
  eleventyConfig.addFilter("renderMarkdown", (value) => {
    if (!value) return "";
    return md.render(String(value));
  });

  // Render parsed Google-style docstring JSON to HTML
  eleventyConfig.addFilter("renderDocstring", (docstring) => {
    if (!docstring) return "";
    let html = "";
    if (docstring.summary) {
      html += `<p class="text-gray-900">${md.renderInline(docstring.summary)}</p>`;
    }
    if (docstring.description) {
      html += `<div class="prose max-w-none mb-3 text-gray-700">${md.render(docstring.description)}</div>`;
    }
    if (docstring.params && docstring.params.length > 0) {
      html += '<h4 class="text-sm font-medium text-gray-60 mb-2">Parameters</h4><dl class="text-sm space-y-2">';
      for (const p of docstring.params) {
        html += '<div class="border-b border-gray-cool-3 pb-2">';
        html += `<dt class="font-mono text-gray-90">${p.name}`;
        if (p.type) html += ` <span class="text-blue-cool-50">: ${p.type}</span>`;
        if (p.default) html += ` <span class="text-gray-500"> = ${p.default}</span>`;
        html += "</dt>";
        if (p.description) html += `<dd class="mt-1 text-gray-60 prose max-w-none">${md.render(p.description)}</dd>`;
        html += "</div>";
      }
      html += "</dl>";
    }
    if (docstring.returns) {
      html += '<h4 class="text-sm font-medium text-gray-60 mb-2 mt-4">Returns</h4><dl class="text-sm space-y-2">';
      html += '<div class="border-b border-gray-cool-3 pb-2">';
      html += "<dt class=\"font-mono text-gray-90\">";
      if (docstring.returns.type) html += `<span class="text-blue-cool-50">${docstring.returns.type}</span>: `;
      html += "</dt>";
      if (docstring.returns.description) html += `<dd class="mt-1 text-gray-60 prose max-w-none">${md.render(docstring.returns.description)}</dd>`;
      html += "</div></dl>";
    }
    if (docstring.raises && docstring.raises.length > 0) {
      html += '<h4 class="text-sm font-medium text-gray-60 mb-2 mt-4">Raises</h4><dl class="text-sm space-y-2">';
      for (const r of docstring.raises) {
        html += '<div class="border-b border-gray-cool-3 pb-2">';
        html += "<dt class=\"font-mono text-gray-90\">";
        if (r.type) html += `<span class="text-blue-cool-50">${r.type}</span>`;
        html += "</dt>";
        if (r.description) html += `<dd class="mt-1 text-gray-60 prose max-w-none">${md.render(r.description)}</dd>`;
        html += "</div>";
      }
      html += "</dl>";
    }
    return html;
  });

  // Basic HTML sanitizer filter to remove dangerous elements and attributes.
  eleventyConfig.addFilter("sanitize", (value) => {
    if (!value) return "";
    let s = String(value);
    return sanitize(s, {
      allowedTags: [
        'p', 'b', 'i', 'em', 'strong', 'a', 'ul', 'ol', 'li', 'br', 'code',
        'dd', 'dl', 'dt', 'detail', 'pre', 'span', 'div', 'h1', 'h2', 'h3',
        'h4', 'h5', 'h6', 'summary',
      ],
      allowedAttributes: {
        'a': ['href', 'title', 'target', 'class'],
        '*': ['class', 'id'],
      },
      allowedTargetBlank: true,
      disallowedTagsMode: 'discard',
    });
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
      ".venv/**",
    ],
  };
};
