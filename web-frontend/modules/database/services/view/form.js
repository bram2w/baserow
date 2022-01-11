export default (client) => {
  return {
    getMetaInformation(slug) {
      return client.get(`/database/views/form/${slug}/submit/`)
    },
    submit(slug, values) {
      return client.post(`/database/views/form/${slug}/submit/`, values)
    },
  }
}
