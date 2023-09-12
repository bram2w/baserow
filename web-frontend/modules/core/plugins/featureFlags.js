import {
  featureFlagIsEnabled,
  getFeatureFlags,
} from '@baserow/modules/core/utils/env'

export default function ({ app }, inject) {
  const FEATURE_FLAGS = getFeatureFlags(app.$config)

  inject('featureFlagIsEnabled', (flag) =>
    featureFlagIsEnabled(FEATURE_FLAGS, flag)
  )
}
