export default (client) => {
  return {
    authorize(integrationId, returnUrl) {
      return client.post(`integration/${integrationId}/oauth2/authorize/`, {
        return_url: returnUrl,
      })
    },
    complete(code, state) {
      return client.post('integration/oauth2/complete/', { code, state })
    },
    getRedirectUri() {
      return client.get('integration/oauth2/redirect-uri/')
    },
  }
}
