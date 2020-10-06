export default (client) => {
  return {
    fetchAll(sortId) {
      return client.get(`/database/views/view/${sortId}/sortings/`)
    },
    create(sortId, values) {
      return client.post(`/database/views/view/${sortId}/sortings/`, values)
    },
    get(viewSortId) {
      return client.get(`/database/views/sort/${viewSortId}/`)
    },
    update(viewSortId, values) {
      return client.patch(`/database/views/sort/${viewSortId}/`, values)
    },
    delete(viewSortId) {
      return client.delete(`/database/views/sort/${viewSortId}/`)
    },
  }
}
