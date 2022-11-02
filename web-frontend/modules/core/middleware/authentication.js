import { getTokenIfEnoughTimeLeft } from '@baserow/modules/core/utils/auth'

export default function ({ store, req, app, route }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // If token is available as query param (e.g. SSO logins) use it.
  // Otherwise try to get the token from the cookie if there is enough time left.
  // for a new session
  let refreshToken = route.query.token
  if (!refreshToken) {
    refreshToken = getTokenIfEnoughTimeLeft(app)
  }

  // If there already is a token we will refresh it to check if it is valid and
  // to get fresh user information. This will probably happen on the server
  // side.
  if (refreshToken && !store.getters['auth/isAuthenticated']) {
    return store.dispatch('auth/refresh', refreshToken)
  }
}
