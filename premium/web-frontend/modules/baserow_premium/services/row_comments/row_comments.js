export default (client) => {
  return {
    fetchAll(tableId, rowId, { offset = 0, limit = 50 }) {
      return client.get(
        `/row_comments/${tableId}/${rowId}/?offset=${offset}&limit=${limit}`
      )
    },
    create(tableId, rowId, message) {
      return client.post(`/row_comments/${tableId}/${rowId}/`, {
        message,
      })
    },
    update(tableId, commentId, message) {
      return client.patch(`/row_comments/${tableId}/comment/${commentId}/`, {
        message,
      })
    },
    delete(tableId, commentId) {
      return client.delete(`/row_comments/${tableId}/comment/${commentId}/`)
    },
    updateNotificationMode(tableId, rowId, mode) {
      return client.put(
        `/row_comments/${tableId}/${rowId}/notification-mode/`,
        { mode }
      )
    },
  }
}
