/**
 * A comma separated list of feature flags used to enable in-progress or not ready
 * features for developers. See docs/development/feature-flags.md for more info
 * @param env: The environment that should be used to get the flags from
 * @returns {string[]}
 */
export function getFeatureFlags(env = process.env) {
  return (env.FEATURE_FLAGS || '')
    .split(',')
    .map((flag) => flag.trim().toLowerCase())
}

/**
 * Checks if a feature is enabled
 * @param featureFlags: The list of feature flags
 * @param flag: The flag that is being checked for
 * @returns {boolean|*}
 */
export function featureFlagIsEnabled(featureFlags, flag) {
  const ENABLE_ALL_FLAG = '*'

  if (featureFlags.includes(ENABLE_ALL_FLAG)) {
    return true
  } else {
    return featureFlags.includes(flag.toLowerCase())
  }
}
