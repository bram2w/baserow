export const VALID_PATH_CHARACTERS =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=".split(
    ''
  )

// This regex needs to be matching PATH_PARAM_REGEX in the backend
// (baserow / contrib / builder / pages / constants.py)
export const PATH_PARAM_REGEX = /(:[A-Za-z0-9_]+)/g

export const ILLEGAL_PATH_SAMPLE_CHARACTER = '^'

/**
 * Get the path parameters from the given path.
 *
 * @param {string} path - The path to extract parameters from.
 * @returns {Array<string>} An array of path parameters.
 */
export function getPathParams(path) {
  return [...path.matchAll(PATH_PARAM_REGEX)].map((pathParam) =>
    pathParam[0].substring(1)
  )
}

/**
 * Split the given path into an array of objects representing its parts.
 * Each part object contains the value and type of the part.
 *
 * @param {string} path - The path to split.
 * @returns {Array<{ value: string, type: string }>} An array of part objects.
 */
export function splitPath(path) {
  const parts = []
  let remainingPath = path || ''

  while (remainingPath.length > 0) {
    const variableMatch = remainingPath.match(PATH_PARAM_REGEX)

    if (variableMatch) {
      const variableIndex = remainingPath.indexOf(variableMatch[0])
      if (variableIndex > 0) {
        const fixedPart = remainingPath.substring(0, variableIndex)
        parts.push({ value: fixedPart, type: 'path' })
      }
      const variablePart = variableMatch[0]
      parts.push({ value: variablePart.substring(1), type: 'variable' })
      remainingPath = remainingPath.substring(
        variableIndex + variablePart.length
      )
    } else {
      parts.push({ value: remainingPath, type: 'path' })
      remainingPath = ''
    }
  }

  return parts
}
