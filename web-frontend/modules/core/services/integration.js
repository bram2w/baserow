export default (client) => {
  return {
    fetchAll(applicationId) {
      return client.get(`application/${applicationId}/integrations/`)
    },
    create(applicationId, integrationType, values, beforeId = null) {
      const payload = {
        type: integrationType,
        ...values,
      }

      if (beforeId !== null) {
        payload.before_id = beforeId
      }

      return client.post(`application/${applicationId}/integrations/`, payload)
    },
    update(integrationId, values) {
      return client.patch(`integration/${integrationId}/`, values)
    },
    delete(integrationId) {
      return client.delete(`integration/${integrationId}/`)
    },
    move(integrationId, beforeId) {
      return client.patch(`integration/${integrationId}/move/`, {
        before_id: beforeId,
      })
    },
  }
}
