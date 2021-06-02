export default (client) => {
  return {
    fetchAll(databaseId) {
      return client.get(`/database/tables/database/${databaseId}/`)
    },
    create(databaseId, values, initialData = null, firstRowHeader = false) {
      if (initialData !== null) {
        values.data = initialData
        values.first_row_header = firstRowHeader
      }

      return client.post(`/database/tables/database/${databaseId}/`, values)
    },
    get(tableId) {
      return client.get(`/database/tables/${tableId}/`)
    },
    update(tableId, values) {
      return client.patch(`/database/tables/${tableId}/`, values)
    },
    order(databaseId, order) {
      return client.post(`/database/tables/database/${databaseId}/order/`, {
        table_ids: order,
      })
    },
    delete(tableId) {
      return client.delete(`/database/tables/${tableId}/`)
    },
  }
}
