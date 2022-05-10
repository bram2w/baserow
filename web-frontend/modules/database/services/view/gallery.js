export default (client) => {
  return {
    fetchRows({
      viewId,
      limit = 100,
      offset = null,
      includeFieldOptions = false,
      search = false,
      signal = null,
    }) {
      const config = {
        params: {
          limit,
        },
      }
      const include = []

      if (signal !== null) {
        config.signal = signal
      }

      if (offset !== null) {
        config.params.offset = offset
      }

      if (includeFieldOptions) {
        include.push('field_options')
      }

      if (include.length > 0) {
        config.params.include = include.join(',')
      }

      if (search) {
        config.params.search = search
      }

      return client.get(`/database/views/gallery/${viewId}/`, config)
    },
    fetchCount({ viewId, search, signal = null }) {
      const config = {
        params: {
          count: true,
        },
      }

      if (signal !== null) {
        config.signal = signal
      }

      if (search) {
        config.params.search = search
      }

      return client.get(`/database/views/gallery/${viewId}/`, config)
    },
  }
}
