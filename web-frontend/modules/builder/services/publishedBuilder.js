export default (client) => {
  return {
    publish(domain) {
      return client.post(`builder/domains/${domain.id}/publish/async/`, {
        domain_id: domain.id,
      })
    },
    fetchByDomain(domain) {
      return client.get(`builder/domains/published/by_name/${domain}/`)
    },
    fetchById(builderId) {
      return client.get(`builder/domains/published/by_id/${builderId}/`)
    },
    fetchElements(page) {
      return client.get(`builder/domains/published/page/${page.id}/elements/`)
    },
    fetchDataSources(pageId) {
      return client.get(
        `builder/domains/published/page/${pageId}/data_sources/`
      )
    },
    fetchWorkflowActions(pageId) {
      return client.get(
        `builder/domains/published/page/${pageId}/workflow_actions/`
      )
    },
    dispatch(dataSourceId, dispatchContext, { range }) {
      // Using POST Http method here is not Restful but it the cleanest way to send
      // data with the call without relying on GET parameter and serialization of
      // complex object.
      const params = {}
      if (range) {
        params.offset = range[0]
        params.count = range[1]
      }

      return client.post(
        `builder/domains/published/data-source/${dataSourceId}/dispatch/`,
        dispatchContext,
        { params }
      )
    },
    dispatchAll(pageId, params) {
      return client.post(
        `builder/domains/published/page/${pageId}/dispatch-data-sources/`,
        params
      )
    },
  }
}
