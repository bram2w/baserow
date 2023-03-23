export default (client) => {
  return {
    create(builderId, name, path) {
      return client.post(`builder/${builderId}/pages/`, { name, path })
    },
    update(pageId, values) {
      return client.patch(`builder/pages/${pageId}/`, values)
    },
    delete(pageId) {
      return client.delete(`builder/pages/${pageId}/`)
    },
    order(builderId, order) {
      return client.post(`/builder/${builderId}/pages/order/`, {
        page_ids: order,
      })
    },
    duplicate(pageId) {
      return client.post(`/builder/pages/${pageId}/duplicate/async/`)
    },
  }
}
