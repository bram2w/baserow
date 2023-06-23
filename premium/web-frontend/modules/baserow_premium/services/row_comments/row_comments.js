export default (client) => {
  return {
    fetchAll(tableId, rowId, { offset = 0, limit = 50 }) {
      return client.get(
        `/row_comments/${tableId}/${rowId}/?offset=${offset}&limit=${limit}`
      )
    },
    create(tableId, rowId, comment) {
      return client.post(`/row_comments/${tableId}/${rowId}/`, { comment })
    },
    update(tableId, commentId, comment) {
      return client.patch(`/row_comments/${tableId}/comment/${commentId}/`, {
        comment,
      })
    },
    delete(tableId, commentId) {
      return client.delete(`/row_comments/${tableId}/comment/${commentId}/`)
    },
  }
}
