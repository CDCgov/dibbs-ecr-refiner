const path = require('path');
const { readJson } = require('./jsonUtils');

const openapiPath = path.join(__dirname, 'openapi.json');

function slugify(method, path) {
  // method + path -> slug-friendly string
  return (method + '-' + path)
    .toLowerCase()
    .replace(/^\/+/, '')
    .replace(/[{}]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)+/g, '');
}
// Resolve $ref to a components.schemas entry
function resolveRef(ref, components) {
  if (!ref || typeof ref !== 'string') return null;
  const m = ref.match(/^#\/components\/schemas\/(.+)$/);
  if (!m) return null;
  return components && components.schemas && components.schemas[m[1]] ? components.schemas[m[1]] : null;
}

// Shallow schema resolver for display purposes. Limits depth to avoid cycles.
function resolveSchema(schema, components, depth = 0) {
  if (!schema || depth > 3) return null;
  const out = {};
  if (schema.$ref) {
    out.ref = schema.$ref;
    const real = resolveRef(schema.$ref, components);
    if (real) {
      const merged = Object.assign({}, real, { description: schema.description || real.description });
      return resolveSchema(merged, components, depth + 1);
    }
    return out;
  }
  out.type = schema.type || null;
  if (schema.title) out.title = schema.title;
  if (schema.description) out.description = schema.description;
  if (schema.enum) out.enum = schema.enum;
  if (out.type === 'object' || schema.properties) {
    const props = schema.properties || {};
    const required = schema.required || [];
    out.properties = Object.entries(props).map(([name, propSchema]) => {
      const resolved = resolveSchema(propSchema, components, depth + 1) || {};
      return {
        name,
        type: resolved.type || propSchema.type || (resolved.ref ? 'ref' : null),
        description: resolved.description || propSchema.description || null,
        required: required.includes(name),
        ref: resolved.ref || null,
      };
    });
  }
  if (out.type === 'array' || schema.items) {
    out.items = resolveSchema(schema.items || {}, components, depth + 1) || null;
  }
  return out;
}

// Only include valid HTTP methods and merge path-level parameters
const httpMethods = ['get','post','put','patch','delete','options','head'];

module.exports = function () {
  const openapi = readJson(openapiPath);

  return Object.entries(openapi.paths || {}).flatMap(([path, methods]) => {
    return Object.entries(methods)
      .filter(([method]) => httpMethods.includes(method.toLowerCase()))
      .map(([method, details]) => {
    // helper: create a lightweight HTML version of a description without
    // running full markdown parsing (avoid defaulting to markdown).
    function safeHtmlFromText(text) {
      if (!text) return "";
      // escape basic HTML chars
      const esc = String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/\'/g, "&#39;");
      // normalize line endings
      const nl = esc.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
      // split into paragraphs by blank line, preserve single-line breaks
      return nl.split(/\n\n+/).map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('\n');
    }

    // normalize responses to an array for easier templating
    const responses = Object.entries(details.responses || {}).map(([code, resp]) => {
      const content = Object.entries(resp.content || {}).map(([media, mediaObj]) => {
        const schema = mediaObj && mediaObj.schema ? mediaObj.schema : null;
        const resolved = schema ? resolveSchema(schema, openapi.components || {}) : null;
        return {
          media,
          // prefer explicit title, fall back to $ref or type
          schemaTitle: schema && schema.title ? schema.title : null,
          schemaRef: schema && schema['$ref'] ? schema['$ref'] : null,
          schemaType: schema && schema.type ? schema.type : null,
          schemaResolved: resolved,
        };
      });

      return {
        code,
        description: resp.description || '',
        content,
      };
    });

    // parameters may exist on operation level or path level; merge them
    const pathParams = (methods.parameters || []) || [];
    const opParams = (details.parameters || []) || [];
    // dedupe by name+in (path-level then op-level) keeping operation-level when duplicates
    const map = new Map();
    pathParams.forEach(p => map.set(`${p.name}|${p.in}`, Object.assign({}, p)));
    opParams.forEach(p => map.set(`${p.name}|${p.in}`, Object.assign({}, p)));
    const params = Array.from(map.values()).map(p => ({ ...p }));

      return {
        path,
        method,
        ...details,
        responses,
        parameters: params,
        // keep raw description text; templates will render via renderTemplate
        // slug used for permalinking (e.g. get-api-v1-conditions-id)
        slug: slugify(method, path),
      };
    });
  }).sort((a, b) => {
    // method-first ordering, then path
    if (a.method === b.method) {
      return a.path.localeCompare(b.path);
    }
    return a.method.localeCompare(b.method);
  });
};
