export default (client) => {
  return {
    fetchRows({
      calendarId,
      limit = 100,
      offset = null,
      includeFieldOptions = false,
      fromTimestamp = null,
      toTimestamp = null,
      userTimeZone = null,
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

      params.append('from_timestamp', fromTimestamp.toISOString())
      params.append('to_timestamp', toTimestamp.toISOString())

      if (userTimeZone) {
        params.append('user_timezone', userTimeZone)
      }

      const config = { params }

      return client.get(`/database/views/calendar/${calendarId}/`, config)
    },
  }
}
