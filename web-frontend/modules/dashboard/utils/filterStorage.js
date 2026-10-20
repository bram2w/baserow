import { shouldResetFilterValues } from '@baserow/modules/dashboard/utils/filter'

const storageKey = (userId, dashboardId) =>
  `baserow.dashboardFilters.${userId}.${dashboardId}`

export function getSavedFilterValues(userId, dashboardId, filters) {
  if (userId == null) return []
  try {
    const saved = JSON.parse(
      sessionStorage.getItem(storageKey(userId, dashboardId))
    )
    if (!Array.isArray(saved)) return []
    return filters.flatMap((filter) => {
      const selection = saved.find((value) => value?.id === filter.id)
      if (
        !selection ||
        !['dropdown', 'input'].includes(selection.mode) ||
        typeof selection.multiple !== 'boolean' ||
        !Array.isArray(selection.values) ||
        !selection.values.every(
          (value) => typeof value === 'string' && value !== ''
        ) ||
        ((filter.mode === 'input' || !filter.multiple) &&
          selection.values.length > 1) ||
        shouldResetFilterValues(selection, filter)
      )
        return []
      return [{ filterId: filter.id, values: selection.values }]
    })
  } catch {
    // Storage can be unavailable or contain an invalid saved selection.
    return []
  }
}

export function saveFilterValues(userId, dashboardId, filters, appliedFilters) {
  if (userId == null) return
  try {
    const selections = filters
      .filter((filter) => appliedFilters[filter.id]?.length)
      .map(({ id, mode, multiple }) => ({
        id,
        mode,
        multiple,
        values: appliedFilters[id],
      }))
    const key = storageKey(userId, dashboardId)
    if (selections.length) {
      sessionStorage.setItem(key, JSON.stringify(selections))
    } else {
      sessionStorage.removeItem(key)
    }
  } catch {
    // Filtering remains available when browser storage is blocked or full.
  }
}
