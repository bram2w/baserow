export default (client) => {
  return {
    fetchAll(viewId) {
      return client.get(`/database/views/${viewId}/filter/`)
    },
    create(viewId, values) {
      return client.post(`/database/views/${viewId}/filters/`, values)
    },
    createGroup(viewId) {
      return client.post(`/database/views/${viewId}/filter-groups/`)
    },
    get(viewFilterId) {
      return client.get(`/database/views/filter/${viewFilterId}/`)
    },
    update(viewFilterId, values) {
      return client.patch(`/database/views/filter/${viewFilterId}/`, values)
    },
    updateGroup(viewFilterGroupId, values) {
      return client.patch(
        `/database/views/filter-group/${viewFilterGroupId}/`,
        values
      )
    },
    delete(viewFilterId) {
      return client.delete(`/database/views/filter/${viewFilterId}/`)
    },
    deleteGroup(viewFilterGroupId) {
      return client.delete(`/database/views/filter-group/${viewFilterGroupId}/`)
    },
  }
}
