export default (client) => {
  return {
    fetchRows({
      viewId,
      limit = 100,
      offset = null,
      includeFieldOptions = false,
      search = false,
      cancelToken = null,
    }) {
      const config = {
        params: {
          limit,
        },
      }
      const include = []

      if (cancelToken !== null) {
        config.cancelToken = cancelToken
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
    fetchCount({ viewId, search, cancelToken = null }) {
      const config = {
        params: {
          count: true,
        },
      }

      if (cancelToken !== null) {
        config.cancelToken = cancelToken
      }

      if (search) {
        config.params.search = search
      }

      return client.get(`/database/views/gallery/${viewId}/`, config)
    },
  }
}
