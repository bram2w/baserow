export default (client) => {
  return {
    async fetchAll(builderId) {
      // TODO Manually add the domain type while the backend doesn't support it.
      const result = await client.get(`builder/${builderId}/domains/`)
      result.data = result.data.map((domain) => ({ type: 'custom', ...domain }))
      return result
    },
    async create(builderId, { type, ...data }) {
      // TODO For now we manage the type manually.
      const result = await client.post(`builder/${builderId}/domains/`, data)
      result.data.type = 'custom'
      return result
    },
    delete(domainId) {
      return client.delete(`builder/domains/${domainId}/`)
    },
  }
}
