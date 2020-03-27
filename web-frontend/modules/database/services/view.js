import { client } from '@baserow/modules/core/services/client'

export default {
  fetchAll(tableId) {
    return client.get(`/database/views/table/${tableId}/`)
  },
  create(tableId, values) {
    return client.post(`/database/views/table/${tableId}/`, values)
  },
  get(viewId) {
    return client.get(`/database/views/${viewId}/`)
  },
  update(viewId, values) {
    return client.patch(`/database/views/${viewId}/`, values)
  },
  delete(viewId) {
    return client.delete(`/database/views/${viewId}/`)
  }
}
