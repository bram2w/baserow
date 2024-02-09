export default (client) => {
  return {
    fetchAll(userSourceId) {
      return client.get(`user_source/${userSourceId}/app_auth_providers/`)
    },
    create(userSourceId, appAuthProviderType, values) {
      const payload = {
        type: appAuthProviderType,
        ...values,
      }

      return client.post(
        `user_source/${userSourceId}/app_auth_providers/`,
        payload
      )
    },
    update(appAuthProviderId, values) {
      return client.patch(`app_auth_provider/${appAuthProviderId}/`, values)
    },
    delete(appAuthProviderId) {
      return client.delete(`app_auth_provider/${appAuthProviderId}/`)
    },
  }
}
