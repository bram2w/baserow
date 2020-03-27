import { client } from '@baserow/modules/core/services/client'

export default {
  create(tableId, values) {
    return client.post(`/database/rows/table/${tableId}/`, values)
  },
  update(tableId, rowId, values) {
    return client.patch(`/database/rows/table/${tableId}/${rowId}/`, values)
  },
  delete(tableId, rowId) {
    return client.delete(`/database/rows/table/${tableId}/${rowId}/`)
  }
}
