export default (client) => {
  return {
    fetchLoginOptions() {
      return client.get('/auth-provider/login-options/')
    },
  }
}
