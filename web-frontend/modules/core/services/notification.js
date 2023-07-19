export default (client) => {
  return {
    fetchAll(workspaceId, { offset = 0, limit = 50 }) {
      return client.get(
        `/notifications/${workspaceId}/?offset=${offset}&limit=${limit}`
      )
    },
    clearAll(workspaceId) {
      return client.delete(`/notifications/${workspaceId}/`)
    },
    markAllAsRead(workspaceId) {
      return client.post(`/notifications/${workspaceId}/mark-all-as-read/`)
    },
    markAsRead(workspaceId, notificationId) {
      return client.patch(`/notifications/${workspaceId}/${notificationId}/`, {
        read: true,
      })
    },
  }
}
