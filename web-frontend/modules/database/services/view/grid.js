export default (client) => {
  return {
    fetchRows({
      gridId,
      limit = 100,
      offset = null,
      cancelToken = null,
      includeFieldOptions = false,
    }) {
      const config = {
        params: {
          limit,
        },
      }
      const includes = []

      if (offset !== null) {
        config.params.offset = offset
      }

      if (cancelToken !== null) {
        config.cancelToken = cancelToken
      }

      if (includeFieldOptions) {
        includes.push('field_options')
      }

      if (includes.length > 0) {
        config.params.includes = includes.join(',')
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
