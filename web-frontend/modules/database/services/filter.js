export default (client) => {
  return {
    fetchAll(viewId) {
      return client.get(`/database/views/view/${viewId}/filter/`)
    },
    create(viewId, values) {
      return client.post(`/database/views/view/${viewId}/filters/`, values)
    },
    get(viewFilterId) {
      return client.get(`/database/views/filter/${viewFilterId}/`)
    },
    update(viewFilterId, values) {
      return client.patch(`/database/views/filter/${viewFilterId}/`, values)
    },
    delete(viewFilterId) {
      return client.delete(`/database/views/filter/${viewFilterId}/`)
    },
  }
}
