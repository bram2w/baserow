/**
 * Clones the provided Javascript object and returns that one.
 *
 * @param o
 * @return {object}
 */
export function clone(o) {
  return JSON.parse(JSON.stringify(o))
}
