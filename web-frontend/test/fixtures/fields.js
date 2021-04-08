export function createFile(visibleName) {
  return {
    url: 'some_url',
    thumbnails: {},
    visible_name: visibleName,
    name: `actual_name_for_${visibleName}`,
    size: 10,
    mime_type: 'text/plain',
    is_image: false,
    image_width: 0,
    image_height: 0,
    uploaded_at: '2019-08-24T14:15:22Z',
  }
}

export function createFields(mock, application, table, fields) {
  let nextId = 1
  const fieldsWithIds = fields.map((f) => ({
    id: nextId++,
    table_id: table.id,
    ...f,
  }))
  mock.onGet(`/database/fields/table/${table.id}/`).reply(200, fieldsWithIds)
  return fieldsWithIds
}
