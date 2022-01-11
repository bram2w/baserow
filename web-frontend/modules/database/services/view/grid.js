export default (client) => {
  return {
    fetchRows({
      gridId,
      limit = 100,
      offset = null,
      cancelToken = null,
      includeFieldOptions = false,
      includeRowMetadata = true,
      search = false,
      publicUrl = false,
      orderBy = '',
      filters = {},
    }) {
      const include = []
      const params = new URLSearchParams()
      params.append('limit', limit)

      if (offset !== null) {
        params.append('offset', offset)
      }

      if (includeFieldOptions) {
        include.push('field_options')
      }

      if (includeRowMetadata) {
        include.push('row_metadata')
      }

      if (include.length > 0) {
        params.append('include', include.join(','))
      }

      if (search) {
        params.append('search', search)
      }

      if (orderBy) {
        params.append('order_by', orderBy)
      }

      Object.keys(filters).forEach((key) => {
        filters[key].forEach((value) => {
          params.append(key, value)
        })
      })

      const config = { params }

      if (cancelToken !== null) {
        config.cancelToken = cancelToken
      }

      const url = publicUrl ? 'public/rows/' : ''
      return client.get(`/database/views/grid/${gridId}/${url}`, config)
    },
    fetchCount({
      gridId,
      search,
      cancelToken = null,
      publicUrl = false,
      filters = {},
    }) {
      const params = new URLSearchParams()
      params.append('count', true)

      if (search) {
        params.append('search', search)
      }

      Object.keys(filters).forEach((key) => {
        filters[key].forEach((value) => {
          params.append(key, value)
        })
      })

      const config = { params }

      if (cancelToken !== null) {
        config.cancelToken = cancelToken
      }

      const url = publicUrl ? 'public/rows/' : ''
      return client.get(`/database/views/grid/${gridId}/${url}`, config)
    },
    filterRows({ gridId, rowIds, fieldIds = null }) {
      const data = { row_ids: rowIds }

      if (fieldIds !== null) {
        data.field_ids = fieldIds
      }

      return client.post(`/database/views/grid/${gridId}/`, data)
    },
    fetchPublicViewInfo(viewSlug) {
      return client.get(`/database/views/grid/${viewSlug}/public/info/`)
    },
  }
}
