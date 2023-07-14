import { notifyIf } from '@baserow/modules/core/utils/error'

export async function openRowEditModal(
  { $store, $router, $route },
  { databaseId, tableId, rowId }
) {
  const tableRoute = $route.name.startsWith('database-table')
  const sameTable = tableRoute && $route.params.tableId === tableId

  // Because 'rowModalNavigation/fetchRow' is called in the asyncData, we need
  // to manually call it here if we are already on the row/table page.
  if (sameTable) {
    try {
      await $store.dispatch('rowModalNavigation/fetchRow', {
        tableId,
        rowId,
      })
    } catch (error) {
      notifyIf(error, 'application')
      return
    }
    const newPath = $router.resolve({
      name: 'database-table-row',
      params: {
        databaseId,
        tableId,
        rowId,
        viewId: $route.params.viewId,
      },
    }).href
    history.replaceState({}, null, newPath)
  } else {
    $router.push({
      name: 'database-table-row',
      params: {
        databaseId,
        tableId,
        rowId,
      },
    })
  }
}
