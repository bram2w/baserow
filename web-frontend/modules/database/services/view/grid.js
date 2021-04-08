export default (client) => {
  return {
    fetchRows({
      gridId,
      limit = 100,
      offset = null,
      cancelToken = null,
      includeFieldOptions = false,
      search = false,
    }) {
      const config = {
        params: {
          limit,
        },
      }
      const include = []

      if (offset !== null) {
        config.params.offset = offset
      }

      if (cancelToken !== null) {
        config.cancelToken = cancelToken
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

      return client.get(`/database/views/grid/${gridId}/`, config)
    },
    fetchCount({ gridId, search, cancelToken = null }) {
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

      return client.get(`/database/views/grid/${gridId}/`, config)
    },
    filterRows({ gridId, rowIds, fieldIds = null }) {
      const data = { row_ids: rowIds }

      if (fieldIds !== null) {
        data.field_ids = fieldIds
      }

      return client.post(`/database/views/grid/${gridId}/`, data)
    },
    update({ gridId, values }) {
      return client.patch(`/database/views/grid/${gridId}/`, values)
    },
  }
}
