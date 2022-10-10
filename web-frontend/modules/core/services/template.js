export default (client) => {
  return {
    fetchAll() {
      return client.get('/templates/')
    },
    install(groupId, templateId) {
      return client.post(`/templates/install/${groupId}/${templateId}/`)
    },
    asyncInstall(groupId, templateId) {
      return client.post(`/templates/install/${groupId}/${templateId}/async/`)
    },
  }
}
