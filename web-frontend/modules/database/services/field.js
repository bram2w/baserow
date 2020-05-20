export default (client) => {
  return {
    fetchAll(tableId) {
      return client.get(`/database/fields/table/${tableId}/`)
    },
    create(tableId, values) {
      return client.post(`/database/fields/table/${tableId}/`, values)
    },
    get(fieldId) {
      return client.get(`/database/fields/${fieldId}/`)
    },
    update(fieldId, values) {
      return client.patch(`/database/fields/${fieldId}/`, values)
    },
    delete(fieldId) {
      return client.delete(`/database/fields/${fieldId}/`)
    },
  }
}
