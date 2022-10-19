export default ({ app }) => {
  // Every time the route changes (fired on initialization too)
  app.router.beforeEach((to, from, next) => {
    if (to.meta.renderInitialChild) {
      next({ name: to.meta.renderInitialChild })
    } else {
      next()
    }
  })
}
