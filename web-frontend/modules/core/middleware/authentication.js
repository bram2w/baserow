import {
  getTokenIfEnoughTimeLeft,
  setToken,
} from '@baserow/modules/core/utils/auth'

export default function ({ store, req, app, route }) {
  // If nuxt generate or already authenticated, pass this middleware
  if ((process.server && !req) || store.getters['auth/isAuthenticated']) return

  // session token (if any) can be in the query param (if SSO) or in the cookies
  let refreshToken = route.query.token
  if (refreshToken) {
    setToken(app, refreshToken)
  } else {
    refreshToken = getTokenIfEnoughTimeLeft(app)
  }
  if (refreshToken) {
    return store.dispatch('auth/refresh', refreshToken)
  }
}
