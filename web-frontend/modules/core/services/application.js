export default (client) => {
  return {
    fetchAll(workspaceId = null) {
      const workspaceUrl =
        workspaceId !== null ? `workspace/${workspaceId}/` : ''
      return client.get(`/applications/${workspaceUrl}`)
    },
    create(workspaceId, values) {
      return client.post(`/applications/workspace/${workspaceId}/`, values)
    },
    asyncDuplicate(applicationId) {
      return client.post(`/applications/${applicationId}/duplicate/async/`)
    },
    get(applicationId) {
      return client.get(`/applications/${applicationId}/`)
    },
    update(applicationId, values) {
      return client.patch(`/applications/${applicationId}/`, values)
    },
    order(workspaceId, order) {
      return client.post(`/applications/workspace/${workspaceId}/order/`, {
        application_ids: order,
      })
    },
    delete(applicationId) {
      return client.delete(`/applications/${applicationId}/`)
    },
  }
}
