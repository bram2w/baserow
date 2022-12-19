export default function ({ app }, inject) {
  // A comma separated list of feature flags used to enable in-progress or not ready
  // features for developers. See docs/development/feature-flags.md for more info.
  const FEATURE_FLAGS = (app.$env.FEATURE_FLAGS || '')
    .split(',')
    .map((flag) => flag.trim().toLowerCase())

  const ENABLE_ALL_FLAG = '*'

  function featureFlagIsEnabled(flag) {
    if (FEATURE_FLAGS.includes(ENABLE_ALL_FLAG)) {
      return true
    } else {
      return FEATURE_FLAGS.includes(flag.toLowerCase())
    }
  }

  inject('featureFlagIsEnabled', featureFlagIsEnabled)
}
