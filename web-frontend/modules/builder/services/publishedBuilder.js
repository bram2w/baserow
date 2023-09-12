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
  }
}
