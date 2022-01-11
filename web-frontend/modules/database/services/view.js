export default (client) => {
  return {
    fetchAll(tableId, includeFilters = false, includeSortings = false) {
      const config = {
        params: {},
      }
      const include = []

      if (includeFilters) {
        include.push('filters')
      }

      if (includeSortings) {
        include.push('sortings')
      }

      if (include.length > 0) {
        config.params.include = include.join(',')
      }

      return client.get(`/database/views/table/${tableId}/`, config)
    },
    create(tableId, values) {
      return client.post(`/database/views/table/${tableId}/`, values)
    },
    get(viewId, includeFilters = false, includeSortings = false) {
      const config = {
        params: {},
      }
      const include = []
      if (includeFilters) {
        include.push('filters')
      }

      if (includeSortings) {
        include.push('sortings')
      }

      if (include.length > 0) {
        config.params.include = include.join(',')
      }
      return client.get(`/database/views/${viewId}/`, config)
    },
    update(viewId, values) {
      return client.patch(`/database/views/${viewId}/`, values)
    },
    order(tableId, order) {
      return client.post(`/database/views/table/${tableId}/order/`, {
        view_ids: order,
      })
    },
    delete(viewId) {
      return client.delete(`/database/views/${viewId}/`)
    },
    fetchFieldOptions(viewId) {
      return client.get(`/database/views/${viewId}/field-options/`)
    },
    updateFieldOptions({ viewId, values }) {
      return client.patch(`/database/views/${viewId}/field-options/`, values)
    },
    rotateSlug(viewId) {
      return client.post(`/database/views/${viewId}/rotate-slug/`)
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
        `/database/views/${slug}/link-row-field-lookup/${fieldId}/`,
        config
      )
    },
  }
}
