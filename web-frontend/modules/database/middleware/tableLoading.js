/**
 * Middleware that changes the table loading state to true before the route
 * changes. That way we can show a loading animation to the user when switching
 * between views.
 */
export default async function ({ route, from, store }) {
  function parseIntOrNull(x) {
    return x != null ? parseInt(x) : null
  }

  const fromTableId = parseIntOrNull(from?.params?.tableId)
  const toTableId = parseIntOrNull(route.params.tableId)
  const differentTableId = fromTableId !== toTableId

  const fromViewId = parseIntOrNull(from?.params?.viewId)
  const toViewId = parseIntOrNull(route.params.viewId)
  const differentViewId = fromViewId !== toViewId

  // Table links might not include the viewId in params (viewId is null), but
  // the end result will be to be redirected to the default view, so don't show
  // the loading animation if that's the case.
  const viewIdToUse = store.getters['view/defaultOrFirst']?.id
  const willRedirectToSameViewId =
    fromViewId && toViewId === null && fromViewId === viewIdToUse

  if (
    !from ||
    differentTableId ||
    (!differentTableId && differentViewId && !willRedirectToSameViewId)
  ) {
    await store.dispatch('table/setLoading', true)
  }
}
