import {
  getTokenIfEnoughTimeLeft,
  setToken,
  userSourceCookieTokenName,
} from '@baserow/modules/core/utils/auth'

export default function ({ store, req, app, route, redirect }) {
  // If nuxt generate or already authenticated, pass this middleware
  if (
    (process.server && !req) ||
    store.getters['userSourceUser/isAuthenticated']
  )
    return

  // token can be in the query string (SSO) or in the cookies (previous session)
  let refreshToken = route.query.token
  if (refreshToken) {
    setToken(app, refreshToken, userSourceCookieTokenName, {
      sameSite: 'Strict',
    })
  } else {
    refreshToken = getTokenIfEnoughTimeLeft(app, userSourceCookieTokenName)
  }

  if (refreshToken) {
    return store
      .dispatch('userSourceUser/refreshAuth', refreshToken)
      .catch((error) => {
        if (error.response?.status === 401) {
          // We logoff as the token has probably expired
          return store.dispatch('userSourceUser/logoff')
        }
      })
  }
}
