export function createGridRows(mock, gridView, fields, rows = []) {
  const fieldOptions = {}
  for (let i = 1; i < fields.length; i++) {
    fieldOptions[i] = {
      width: 200,
      hidden: false,
      order: i,
    }
  }
  mock.onGet(`/database/views/grid/${gridView.id}/`).reply(200, {
    count: rows.length,
    results: rows,
    field_options: fieldOptions,
  })
}

export function createPublicGridViewRows(mock, viewSlug, fields, rows = []) {
  const fieldOptions = {}
  for (let i = 1; i < fields.length; i++) {
    fieldOptions[i] = {
      width: 200,
      hidden: false,
      order: i,
    }
  }
  mock.onGet(`/database/views/grid/${viewSlug}/public/rows/`).reply(200, {
    count: rows.length,
    results: rows,
    field_options: fieldOptions,
  })
}

export function deleteGridRow(mock, tableId, rowId, responseCode = 204) {
  mock.onDelete(`/database/rows/table/${tableId}/${rowId}/`).reply(responseCode)
}
