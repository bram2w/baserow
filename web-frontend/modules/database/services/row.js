let pendingGetQueries = {}
let delay = null
const GRACE_DELAY = 50 // ms before querying the backend with a get query

export default (client) => {
  const getNameCallback = async () => {
    const config = {}
    config.params = Object.fromEntries(
      Object.entries(pendingGetQueries).map(([tableId, rows]) => {
        const rowIds = Object.keys(rows)
        return [`table__${tableId}`, rowIds.join(',')]
      })
    )

    const { data } = await client.get(`/database/rows/names/`, config)

    Object.entries(data).forEach(([tableId, rows]) => {
      Object.entries(rows).forEach(([rowId, rowName]) => {
        pendingGetQueries[tableId][rowId].forEach((resolve) => resolve(rowName))
      })
    })
    pendingGetQueries = {}
    delay = null
  }

  return {
    get(tableId, rowId) {
      return client.get(`/database/rows/table/${tableId}/${rowId}/`)
    },
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
    /**
     * Returns the name of specified table row. Batch consecutive queries into one
     * during the defined GRACE_TIME.
     */
    getName(tableId, rowId) {
      return new Promise((resolve) => {
        clearTimeout(delay)

        if (!pendingGetQueries[tableId]) {
          pendingGetQueries[tableId] = {}
        }
        if (!pendingGetQueries[tableId][rowId]) {
          pendingGetQueries[tableId][rowId] = []
        }
        pendingGetQueries[tableId][rowId].push(resolve)

        delay = setTimeout(getNameCallback, GRACE_DELAY)
      })
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
    batchUpdate(tableId, items) {
      return client.patch(`/database/rows/table/${tableId}/batch/`, { items })
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
    batchDelete(tableId, items) {
      return client.post(`/database/rows/table/${tableId}/batch-delete/`, {
        items,
      })
    },
  }
}
