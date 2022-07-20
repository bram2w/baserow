/**
 * Find the primary field in a list of fields.
 * If no primary field is found, return the first field.
 * @param fields
 * @returns {*}
 */
export function getPrimaryOrFirstField(fields) {
  const primaryField = fields.find((field) => field.primary)
  return primaryField || fields[0]
}
