export default (client) => {
  return {
    fetchRows({
      kanbanId,
      limit = 100,
      offset = null,
      cancelToken = null,
      includeFieldOptions = false,
      selectOptions = [],
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

      if (include.length > 0) {
        params.append('include', include.join(','))
      }

      selectOptions.forEach((selectOption) => {
        let value = selectOption.id.toString()
        if (Object.prototype.hasOwnProperty.call(selectOption, 'limit')) {
          value += `,${selectOption.limit}`
          if (Object.prototype.hasOwnProperty.call(selectOption, 'offset')) {
            value += `,${selectOption.offset}`
          }
        }
        params.append('select_option', value)
      })

      const config = { params }

      if (cancelToken !== null) {
        config.cancelToken = cancelToken
      }

      return client.get(`/database/views/kanban/${kanbanId}/`, config)
    },
  }
}
