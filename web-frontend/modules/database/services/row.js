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
    /**
     * Moves the row to the position before the row related to the beforeRowId
     * parameters. If the before id is not provided then the row will be moved
     * to the end.
     */
    move(tableId, rowId, beforeRowId = null) {
      const config = { params: {} }

      if (beforeRowId !== null) {
        config.params.before_id = beforeRowId
      }

      return client.patch(
        `/database/rows/table/${tableId}/${rowId}/move/`,
        null,
        config
      )
    },
    delete(tableId, rowId) {
      return client.delete(`/database/rows/table/${tableId}/${rowId}/`)
    },
  }
}
