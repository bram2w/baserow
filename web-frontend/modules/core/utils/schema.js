/**
 * Extracts a sub-schema from a JSON schema based on a given path.
 *
 * This function recursively traverses a JSON schema to locate and return
 * a sub-schema that corresponds to the specified path. The path is an array
 * of strings, where each string represents a key in the schema's properties.
 *
 * If the schema at any level is an array, the function automatically
 * continues traversal within the `items` schema of the array. If the path is
 * invalid (i.e., the specified property does not exist), the function returns `null`.
 *
 * @param {Object} schema - The JSON schema object to extract from.
 * @param {Array<string>} path - An array of strings representing the path
 *     to the desired sub-schema. For example, `['address', 'street']`.
 * @returns {Object|null} - The extracted sub-schema, or `null` if the path is invalid.
 *
 * @example
 * const schema = {
 *   type: 'object',
 *   properties: {
 *     name: { type: 'string' },
 *     address: {
 *       type: 'object',
 *       properties: {
 *         street: { type: 'string' },
 *         city: { type: 'string' },
 *       },
 *     },
 *   },
 * };
 * const path = ['address', 'street'];
 * const subSchema = extractSubSchema(schema, path);
 * console.log(subSchema); // { type: 'string' }
 */
export function extractSubSchema(schema, path) {
  const [first, ...rest] = path
  if (!first) {
    return schema
  } else {
    if (schema.type === 'array' && schema.items) {
      schema = schema.items
    }
    if (schema.properties && schema.properties[first]) {
      return extractSubSchema(schema.properties[first], rest)
    } else {
      return null // If the path is invalid, return null
    }
  }
}
