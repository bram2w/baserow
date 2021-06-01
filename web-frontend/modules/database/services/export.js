export default (client) => {
  return {
    export(tableId, values) {
      return client.post(`/database/export/table/${tableId}/`, {
        ...values,
      })
    },
    get(jobId) {
      return client.get(`/database/export/${jobId}/`)
    },
  }
}
