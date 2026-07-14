const { EleventyRenderPlugin } = require("@11ty/eleventy");
const markdownIt = require("markdown-it");
const sanitize = require("sanitize-html");
const fs = require("fs");
const path = require("path");
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

  // Render root README.md for the onboarding page:
  //   - strips the first # Title line
  //   - rewrites relative URLs to GitHub absolute URLs
  //   - converts GitHub admonitions to styled HTML
  //   - renders remaining markdown through markdown-it
  eleventyConfig.addFilter("renderReadme", (value) => {
    if (!value) return "";
    const GITHUB_BASE = "https://github.com/CDCgov/dibbs-ecr-refiner/blob/main";
    let content = String(value);

    // 1. Rewrite relative URLs in markdown links and images
    content = content.replace(
      /(!?\[[^\]]*\]\()([^)]+)(\))/g,
      (match, prefix, url, suffix) => {
        if (url.startsWith("http") || url.startsWith("#") || url.startsWith("mailto:")) {
          return match;
        }
        const clean = url.replace(/^[.\/]+/, "");
        return `${prefix}${GITHUB_BASE}/${clean}${suffix}`;
      }
    );

    // 2. Convert GitHub admonitions to styled HTML
    content = content.replace(
      /^> \[!(\w+)\]\n((?:^> .*\n?)*)/gm,
      (match, type, inner) => {
        const rendered = md.render(inner.replace(/^> /gm, ""));
        const colors = {
          NOTE: "border-blue-500 bg-blue-50",
          TIP: "border-green-500 bg-green-50",
          IMPORTANT: "border-purple-500 bg-purple-50",
          WARNING: "border-yellow-500 bg-yellow-50",
          CAUTION: "border-red-500 bg-red-50",
        };
        const cls = colors[type.toUpperCase()] || "border-gray-500 bg-gray-50";
        return `<div class="border-l-4 ${cls} px-4 py-3 my-4"><p class="font-bold text-sm uppercase tracking-wide mb-1">${type}</p>${rendered}</div>\n`;
      }
    );

    // 3. Render remaining markdown
    return md.render(content);
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
        'h4', 'h5', 'h6', 'summary', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
      ],
      allowedAttributes: {
        'a': ['href', 'title', 'target', 'class'],
        '*': ['class', 'id'],
      },
      allowedTargetBlank: true,
      disallowedTagsMode: 'discard',
    });
  });

  // Filter an array by a property value. Usage: items | where: "prop", "value"
  eleventyConfig.addFilter("where", (array, key, value) => {
    if (!Array.isArray(array)) return [];
    return array.filter(item => item[key] === value);
  });

  // Collection of ADR files with parsed metadata (title, date, number, status)
  eleventyConfig.addCollection("decisions", function(collectionApi) {
    return collectionApi.getFilteredByGlob("decisions/*.md").map(function(item) {
      var fullPath = path.join(__dirname, item.inputPath);
      var content = fs.readFileSync(fullPath, "utf-8");
      var lines = content.split("\n");

      // Parse "# N: Title" or "# N. Title"
      var titleMatch = lines[0].match(/^#\s+\d+[\.:]\s*(.+)/);
      var title = titleMatch ? titleMatch[1].trim() : "Unknown";

      // Parse date (supports "Date:" and "**Date:**" formats)
      var dateMatch = null;
      for (var di = 1; di < Math.min(lines.length, 6); di++) {
        dateMatch = lines[di].match(/(?:\*{2})?Date(?:\*{2})?:(?:\*{2})?\s*(.+)/);
        if (dateMatch) break;
      }
      var date = dateMatch ? dateMatch[1].trim() : "";

      // Parse status (supports "## Status" and "**Status:**" formats)
      var status = "";
      for (var i = 1; i < Math.min(lines.length, 12); i++) {
        var trimmed = lines[i].trim();
        // Inline format: "**Status:** Accepted"
        var inlineMatch = trimmed.match(/^\*\*Status:\*?\*?\s+(.+)/);
        if (inlineMatch) {
          status = inlineMatch[1].trim();
          break;
        }
        // Section format: "## Status" then next non-empty line
        if (trimmed === "## Status") {
          for (var j = i + 1; j < Math.min(lines.length, 14); j++) {
            if (lines[j].trim()) {
              status = lines[j].trim();
              break;
            }
          }
          break;
        }
      }

      return {
        url: item.url,
        title: title,
        date: date,
        number: parseInt(item.fileSlug.split("_")[0], 10),
        status: status,
      };
    }).sort(function(a, b) {
      // Sort descending by number (newest first)
      return b.number - a.number;
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
