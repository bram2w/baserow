import { client } from '@baserow/modules/core/services/client'

export default {
  fetchRows({ gridId, limit = 100, offset = null, cancelToken = null }) {
    const config = {
      params: {
        limit: limit
      }
    }

    if (offset !== null) {
      config.params.offset = offset
    }

    if (cancelToken !== null) {
      config.cancelToken = cancelToken
    }

    return client.get(`/database/views/grid/${gridId}/`, config)
  }
}
