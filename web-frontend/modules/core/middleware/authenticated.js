/**
 * If this middleware is added to a page, it will redirect back to the login
 * page if the user is not authenticated.
 */
export default function ({ req, store, route, redirect }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  if (!store.getters['auth/isAuthenticated']) {
    const query = {}
    if (req) {
      query.original = encodeURI(req.originalUrl)
    } else {
      query.original = route.path
    }

    return redirect({ name: 'login', query })
  }
}
