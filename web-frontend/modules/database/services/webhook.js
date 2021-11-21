export default (client) => {
  return {
    fetchAll(tableId) {
      return client.get(`/database/webhooks/table/${tableId}/`)
    },
    create(tableId, values) {
      return client.post(`/database/webhooks/table/${tableId}/`, values)
    },
    get(webhookId) {
      return client.get(`/database/webhooks/${webhookId}/`)
    },
    update(webhookId, values) {
      return client.patch(`/database/webhooks/${webhookId}/`, values)
    },
    delete(webhookId) {
      return client.delete(`/database/webhooks/${webhookId}/`)
    },
    testCall(tableId, values) {
      return client.post(
        `/database/webhooks/table/${tableId}/test-call/`,
        values
      )
    },
  }
}
