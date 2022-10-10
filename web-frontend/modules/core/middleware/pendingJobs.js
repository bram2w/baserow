/**
 * If this middleware is added to a page, it will load the pending jobs
 * for the user from the server in order to show them in the UI.
 */
export default async function ({ req, store }) {
  // If nuxt generate, pass this middleware
  if (process.server && !req) return

  // If the user is not authenticated we will redirect him to the login page.
  if (store.getters['auth/isAuthenticated']) {
    await store.dispatch('job/fetchAllUnfinished')
  }
}
