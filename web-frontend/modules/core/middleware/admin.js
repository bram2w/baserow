/**
 * This middleware makes sure that the current user is admin else a 403 error
 * will be shown to the user.
 */
export default function ({ store, req, error }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  const selectedGroup = store.getters['group/selectedGroup']

  // If the user is not staff we want to show a forbidden error.
  if (selectedGroup.permissions !== 'ADMIN') {
    return error({ statusCode: 403, message: 'Forbidden.' })
  }
}
