export default (client) => {
  return {
    getMetaInformation(slug) {
      return client.get(`/database/views/form/${slug}/submit/`)
    },
    submit(slug, values) {
      return client.post(`/database/views/form/${slug}/submit/`, values)
    },
    linkRowFieldLookup(slug, fieldId, page, search = null) {
      const config = {
        params: {
          page,
          size: 100,
        },
      }

      if (search !== null) {
        config.params.search = search
      }

      return client.get(
        `/database/views/form/${slug}/link-row-field-lookup/${fieldId}/`,
        config
      )
    },
  }
}
