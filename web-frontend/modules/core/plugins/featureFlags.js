import {
  featureFlagIsEnabled,
  getFeatureFlags,
} from '@baserow/modules/core/utils/env'

export default function ({ app }, inject) {
  const FEATURE_FLAGS = getFeatureFlags(app.$env)

  inject('featureFlagIsEnabled', (flag) =>
    featureFlagIsEnabled(FEATURE_FLAGS, flag)
  )
}
