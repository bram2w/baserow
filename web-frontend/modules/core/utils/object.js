/**
 * Clones the provided Javascript object and returns that one.
 *
 * @param o
 * @return {object}
 */
export function clone(o) {
  return JSON.parse(JSON.stringify(o))
}

/**
 * Creates an object where the key indicates the line number and the value is
 * the string that must be shown on that line number. The line number matches
 * the line number if the value would be stringified with an indent of 4
 * characters `JSON.stringify(value, null, 4)`. The correct value is matched
 * if a value (recursive) object key matches a key of the mapping. However values will
 * not be matched inside the children of a matching key.
 *
 * Example:
 * mappingToStringifiedJSONLines(
 *  { key_2: 'Value' },
 *  {
 *    key_1: 'A random value',
 *    key_2: 'Another value'
 *  }
 * ) === {
 *   3: 'Value'
 * }
 */
export function mappingToStringifiedJSONLines(
  mapping,
  value,
  index = 1,
  lines = {},
  first = true
) {
  if (Array.isArray(value)) {
    index += 1
    value.forEach((v, i) => {
      index = mappingToStringifiedJSONLines(mapping, v, index, lines, false)
    })
    index += 1
    return first ? lines : index
  } else if (value instanceof Object) {
    index += 1
    Object.keys(value).forEach((k) => {
      let childMapping = mapping
      if (Object.prototype.hasOwnProperty.call(mapping, k)) {
        lines[index] = mapping[k]
        // Only recursively search for more field to line mappings where the current key
        // is not itself the key for a field.
        // For example if this key is a field, then there cannot be any other fields
        // to map within this fields value.
        childMapping = {}
      }
      index = mappingToStringifiedJSONLines(
        childMapping,
        value[k],
        index,
        lines,
        false
      )
    })
    index += 1
    return first ? lines : index
  } else {
    index += 1
    return first ? lines : index
  }
}

export function isPromise(p) {
  return (
    p !== null &&
    typeof p === 'object' &&
    typeof p.then === 'function' &&
    typeof p.catch === 'function'
  )
}
