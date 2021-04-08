export default (client) => {
  return {
    fetchAll() {
      return client.get('/templates/')
    },
    install(groupId, templateId) {
      return client.get(`/templates/install/${groupId}/${templateId}/`)
    },
  }
}
