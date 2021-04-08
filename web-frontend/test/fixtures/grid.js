export function createRows(mock, gridView, fields, rows = []) {
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
