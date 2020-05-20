export default (client) => {
  return {
    login(username, password) {
      return client.post('/user/token-auth/', {
        username,
        password,
      })
    },
    refresh(token) {
      return client.post('/user/token-refresh/', {
        token,
      })
    },
    register(email, name, password, authenticate = true) {
      return client.post('/user/', {
        name,
        email,
        password,
        authenticate,
      })
    },
    sendResetPasswordEmail(email, baseUrl) {
      return client.post('/user/send-reset-password-email/', {
        email,
        base_url: baseUrl,
      })
    },
    resetPassword(token, password) {
      return client.post('/user/reset-password/', {
        token,
        password,
      })
    },
  }
}
