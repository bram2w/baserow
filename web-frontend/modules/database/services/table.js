import { client } from '@baserow/modules/core/services/client'

export default {
  fetchAll(databaseId) {
    return client.get(`/database/tables/database/${databaseId}/`)
  },
  create(databaseId, values) {
    return client.post(`/database/tables/database/${databaseId}/`, values)
  },
  get(tableId) {
    return client.get(`/database/tables/${tableId}/`)
  },
  update(tableId, values) {
    return client.patch(`/database/tables/${tableId}/`, values)
  },
  delete(tableId) {
    return client.delete(`/database/tables/${tableId}/`)
  },
}
