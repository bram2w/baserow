export default (client) => {
  return {
    fetchRows({ gridId, limit = 100, offset = null, cancelToken = null }) {
      const config = {
        params: {
          limit,
        },
      }

      if (offset !== null) {
        config.params.offset = offset
      }

      if (cancelToken !== null) {
        config.cancelToken = cancelToken
      }

      return client.get(`/database/views/grid/${gridId}/`, config)
    },
  }
}
