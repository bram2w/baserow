export default (client) => {
  return {
    fetchAll(builderId) {
      return client.get(`builder/${builderId}/domains/`)
    },
    create(builderId, data) {
      return client.post(`builder/${builderId}/domains/`, data)
    },
    delete(domainId) {
      return client.delete(`builder/domains/${domainId}/`)
    },
  }
}
