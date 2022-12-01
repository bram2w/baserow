export default (client) => {
  return {
    login(email, password) {
      return client.post('/user/token-auth/', { email, password })
    },
    refresh(refreshToken) {
      return client.post(
        '/user/token-refresh/',
        { refresh_token: refreshToken },
        { skipAuthRefresh: true }
      )
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
    deleteAccount() {
      return client.post('/user/schedule-account-deletion/')
    },
  }
}
