export default (client) => {
  return {
    fetchAll() {
      return client.get('/templates/')
    },
    fetchOwn({ offset = 0, limit = 20, search = '' } = {}) {
      const params = { offset, limit }
      if (search) {
        params.search = search
      }
      return client.get('/templates/own/', { params })
    },
    fetch(slug) {
      return client.get(`/templates/${slug}/`)
    },
    install(workspaceId, templateId) {
      return client.post(`/templates/install/${workspaceId}/${templateId}/`)
    },
    asyncInstall(workspaceId, templateId) {
      return client.post(
        `/templates/install/${workspaceId}/${templateId}/async/`
      )
    },
  }
}
