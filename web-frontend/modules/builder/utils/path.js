export const VALID_PATH_CHARACTERS =
  "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~:/?#[]@!$&'()*+,;=".split(
    ''
  )

// This regex needs to be matching PATH_PARAM_REGEX in the backend
// (baserow / contrib / builder / pages / constants.py)
export const PATH_PARAM_REGEX = /(:[A-Za-z0-9_]+)/g

export const ILLEGAL_PATH_SAMPLE_CHARACTER = '^'

export function getPathParams(path) {
  return [...path.matchAll(PATH_PARAM_REGEX)].map((pathParam) =>
    pathParam[0].substring(1)
  )
}
