/**
 * Responsible for returning the default value for a parameter,
 * based on the parameter's type.
 *
 * @param type The parameter's type (e.g. `text` or `numeric`).
 * @returns {String} The default value.
 */
export function defaultValueForParameterType(type) {
  return type === 'numeric' ? 1 : 'test'
}
