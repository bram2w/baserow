export default function ({ app }, inject) {
  const { $registry } = app
  function hasFeature(feature, forSpecificWorkspace) {
    return Object.values($registry.getAll('plugin')).some((p) =>
      p.hasFeature(feature, forSpecificWorkspace)
    )
  }
  inject('hasFeature', hasFeature)
}
