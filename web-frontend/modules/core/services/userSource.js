export default (client) => {
  return {
    fetchAll(applicationId) {
      return client.get(`application/${applicationId}/user_sources/`)
    },
    create(applicationId, userSourceType, values, beforeId = null) {
      const payload = {
        type: userSourceType,
        ...values,
      }

      if (beforeId !== null) {
        payload.before_id = beforeId
      }

      return client.post(`application/${applicationId}/user_sources/`, payload)
    },
    update(userSourceId, values) {
      return client.patch(`user_source/${userSourceId}/`, values)
    },
    delete(userSourceId) {
      return client.delete(`user_source/${userSourceId}/`)
    },
    move(userSourceId, beforeId) {
      return client.patch(`user_source/${userSourceId}/move/`, {
        before_id: beforeId,
      })
    },
  }
}
