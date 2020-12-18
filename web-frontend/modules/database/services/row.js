export default (client) => {
  return {
    fetchAll({ tableId, page = 1, size = 10, search = null }) {
      const config = {
        params: {
          page,
          size,
        },
      }

      if (search !== null && search !== '') {
        config.params.search = search
      }

      return client.get(`/database/rows/table/${tableId}/`, config)
    },
    create(tableId, values, beforeId = null) {
      const config = { params: {} }

      if (beforeId !== null) {
        config.params.before = beforeId
      }

      return client.post(`/database/rows/table/${tableId}/`, values, config)
    },
    update(tableId, rowId, values) {
      return client.patch(`/database/rows/table/${tableId}/${rowId}/`, values)
    },
    delete(tableId, rowId) {
      return client.delete(`/database/rows/table/${tableId}/${rowId}/`)
    },
  }
}
