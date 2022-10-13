/**
 * This middleware makes sure that the current user is staff else a 403 error
 * will be shown to the user.
 */
export default function ({ store, req, error }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // If the user is not staff we want to show a forbidden error.
  if (!store.getters['auth/isStaff']) {
    return error({ statusCode: 403, message: 'Forbidden.' })
  }
}
