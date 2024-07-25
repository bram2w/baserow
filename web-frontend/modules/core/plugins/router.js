import VueRouter from 'vue-router'

export default function ({ app }) {
  const originalPush = app.router.push

  app.router.push = async function push(...args) {
    try {
      return await originalPush.call(this, ...args)
    } catch (error) {
      // When navigating to a page, it can happen that it redirects to another one.
      // For some reason, this is causing the router throw an error. In our case, it's
      // perfectly fine, so we're suppressing this error here. More information:
      // https://stackoverflow.com/questions/62223195/vue-router-uncaught-in-promise-
      // error-redirected-from-login-to-via-a
      const { isNavigationFailure, NavigationFailureType } = VueRouter
      if (!isNavigationFailure(error, NavigationFailureType.redirected)) {
        throw error
      }
    }
  }
}
