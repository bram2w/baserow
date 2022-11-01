export default (client) => {
  return {
    fetchAll() {
      return client.get('/admin/auth-provider/')
    },
    fetch(id) {
      return client.get(`/admin/auth-provider/${id}/`)
    },
    create(values) {
      return client.post('/admin/auth-provider/', values)
    },
    update(id, values) {
      return client.patch(`/admin/auth-provider/${id}/`, values)
    },
    delete(id) {
      return client.delete(`/admin/auth-provider/${id}/`)
    },
    fetchNextProviderId() {
      return client.get(`/admin/auth-provider/next-id/`)
    },
  }
}
