import { PUBLIC_PLACEHOLDER_ENTITY_ID } from '@baserow/modules/database/utils/constants'

export function createPublicGridView(
  mock,
  viewSlug,
  { name, fields = [], sortings = [] }
) {
  if (name === undefined) {
    name = `public_mock_view_${viewSlug}`
  }
  const publicGridView = {
    id: viewSlug,
    table: {
      id: PUBLIC_PLACEHOLDER_ENTITY_ID,
      database_id: PUBLIC_PLACEHOLDER_ENTITY_ID,
    },
    order: 0,
    name,
    type: 'grid',
    public: true,
    slug: viewSlug,
    sortings,
  }
  mock
    .onGet(`/database/views/grid/${viewSlug}/public/info/`)
    .reply(200, { view: publicGridView, fields })
}

export function createGridView(
  mock,
  application,
  table,
  { viewType = 'grid', viewId = 1, filters = [], publicView = false }
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
    public: publicView,
    filters,
  }
  mock.onGet(`/database/views/table/${tableId}/`).reply(200, [gridView])
  return gridView
}
