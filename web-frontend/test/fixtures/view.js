export function createGridView(
  mock,
  application,
  table,
  { viewType = 'grid', viewId = 1, filters = [] }
) {
  const tableId = table.id
  const gridView = {
    id: viewId,
    table_id: tableId,
    name: `mock_view_${viewId}`,
    order: 0,
    type: viewType,
    table: {
      id: tableId,
      name: table.name,
      order: 0,
      database_id: application.id,
    },
    filter_type: 'AND',
    filters_disabled: false,
    filters,
  }
  mock.onGet(`/database/views/table/${tableId}/`).reply(200, [gridView])
  return gridView
}
