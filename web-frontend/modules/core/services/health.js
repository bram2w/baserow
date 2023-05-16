export default (client) => {
  return {
    getAll() {
      return client.get('/_health/full/')
    },
    testEmail(targetEmail) {
      return client.post('/_health/email/', {
        target_email: targetEmail,
      })
    },
  }
}
