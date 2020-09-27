export default (client) => {
  return {
    fetchAll(tableId, includeFilters = false) {
      const config = {
        params: {},
      }
      const includes = []

      if (includeFilters) {
        includes.push('filters')
      }

      if (includes.length > 0) {
        config.params.includes = includes.join(',')
      }

      return client.get(`/database/views/table/${tableId}/`, config)
    },
    create(tableId, values) {
      return client.post(`/database/views/table/${tableId}/`, values)
    },
    get(viewId) {
      return client.get(`/database/views/${viewId}/`)
    },
    update(viewId, values) {
      return client.patch(`/database/views/${viewId}/`, values)
    },
    delete(viewId) {
      return client.delete(`/database/views/${viewId}/`)
    },
  }
}
