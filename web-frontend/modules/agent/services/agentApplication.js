export default (client) => ({
  get(agentId) {
    return client.get(`/agent/${agentId}/`)
  },
})
