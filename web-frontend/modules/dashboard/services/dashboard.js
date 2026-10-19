export default (client) => {
  return {
    rotateSlug(dashboardId) {
      return client.post(`/dashboard/${dashboardId}/rotate-slug/`)
    },
  }
}
