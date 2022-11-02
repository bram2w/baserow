/**
 * If this middleware is added to a page, it will redirect back to the login
 * page if the user is not authenticated.
 */
export default function ({ req, store, route, redirect }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // If the user is not authenticated we will redirect him to the login page.
  if (!store.getters['auth/isAuthenticated']) {
    const query = {}
    if (req) {
      query.original = encodeURI(req.originalUrl)
    }

    return redirect({ name: 'login', query })
  }

  // remove the token if encoded in the URL and continue to the requested page.
  if (route.query.token) {
    delete route.query.token
    return redirect({ path: route.path, query: route.query })
  }
}
