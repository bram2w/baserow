export default (client) => {
  return {
    getSamlLoginUrl({ email, original }) {
      return client.get(`/sso/saml/login-url/`, { params: { email, original } })
    },
  }
}
