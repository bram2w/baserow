export default (client) => {
  return {
    fetchAll(pageId) {
      return client.get(`builder/page/${pageId}/data-sources/`)
    },
    create(pageId, values = {}, beforeId = null) {
      const payload = {
        page_id: pageId,
        ...values,
      }

      if (beforeId !== null) {
        payload.before_id = beforeId
      }

      return client.post(`builder/page/${pageId}/data-sources/`, payload)
    },
    update(dataSourceId, values) {
      return client.patch(`builder/data-source/${dataSourceId}/`, values)
    },
    delete(dataSourceId) {
      return client.delete(`builder/data-source/${dataSourceId}/`)
    },
    move(dataSourceId, beforeId) {
      return client.patch(`builder/data-source/${dataSourceId}/move/`, {
        before_id: beforeId,
      })
    },
    dispatch(dataSourceId, params) {
      // Using POST Http method here is not Restful but it the cleanest way to send
      // data with the call without relying on GET parameter and serialization of
      // complex object.
      return client.post(
        `builder/data-source/${dataSourceId}/dispatch/`,
        params
      )
    },
    dispatchAll(pageId, params) {
      return client.post(
        `builder/page/${pageId}/dispatch-data-sources/`,
        params
      )
    },
  }
}
