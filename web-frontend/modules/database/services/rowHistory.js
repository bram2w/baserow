export default (client) => {
  return {
    fetchAll({ tableId, rowId, limit, offset }) {
      return client.get(`/database/rows/table/${tableId}/${rowId}/history/`, {
        params: {
          limit,
          offset,
        },
      })
    },
  }
}
