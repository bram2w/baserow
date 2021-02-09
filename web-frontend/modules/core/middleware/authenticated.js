/**
 * If this middleware is added to a page, it will redirect back to the login
 * page if the user is not authenticated.
 */
export default function ({ req, store, redirect }) {
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
}
