export default function ({ app }, inject) {
  // A comma separated list of feature flags used to enable in-progress or not ready
  // features for developers. See docs/development/feature-flags.md for more info.
  const FEATURE_FLAGS = (app.$env.FEATURE_FLAGS || '')
    .split(',')
    .map((flag) => flag.trim())
  inject('featureFlags', FEATURE_FLAGS)
}
