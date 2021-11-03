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
    register(
      email,
      name,
      password,
      language,
      authenticate = true,
      groupInvitationToken = null,
      templateId = null
    ) {
      const values = {
        name,
        email,
        password,
        authenticate,
        language,
      }

      if (groupInvitationToken !== null) {
        values.group_invitation_token = groupInvitationToken
      }

      if (templateId !== null) {
        values.template_id = templateId
      }

      return client.post('/user/', values)
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
    changePassword(oldPassword, newPassword) {
      return client.post('/user/change-password/', {
        old_password: oldPassword,
        new_password: newPassword,
      })
    },
    dashboard() {
      return client.get('/user/dashboard/')
    },
    update(values) {
      return client.patch('/user/account/', values)
    },
  }
}
