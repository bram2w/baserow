/**
 * Middleware that changes the table loading state to true before the the route
 * changes. That way we can show a loading animation to the user when switching
 * between views.
 */
export default async function ({ store }) {
  await store.dispatch('table/setLoading', true)
}
