import { getToken } from '@baserow/modules/core/utils/auth'

export default function ({ store, req, app }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // Load the token
  const token = getToken(app)

  // If there already is a token we will refresh it to check if it is valid and
  // to get fresh user information. This will probably happen on the server
  // side.
  if (token && !store.getters['auth/isAuthenticated']) {
    return store.dispatch('auth/refresh', token)
  }
}
