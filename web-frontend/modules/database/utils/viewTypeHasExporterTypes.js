/**
 * Check if the view of type viewType has at least a valid exporter.
 */
export default function (viewType, registry) {
  const exporters = Object.values(registry.getAll('exporter'))
  for (let i = 0; i < exporters.length; i++) {
    if (exporters[i].getSupportedViews().includes(viewType)) {
      return true
    }
  }
  return false
}
