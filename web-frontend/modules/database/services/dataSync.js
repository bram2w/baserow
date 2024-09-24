export default (client) => {
  return {
    create(databaseId, values) {
      return client.post(`/database/data-sync/database/${databaseId}/`, values)
    },
    syncTable(dataSyncId) {
      return client.post(`/database/data-sync/${dataSyncId}/sync/async/`)
    },
    fetchProperties(values) {
      return client.post(`/database/data-sync/properties/`, values)
    },
  }
}
