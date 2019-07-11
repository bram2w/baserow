import { client } from '@/services/client'

export default function({ store }) {
  // Create a request interceptor to add the authorization token to every
  // request if the user is authenticated.
  client.interceptors.request.use(config => {
    if (store.getters['auth/isAuthenticated']) {
      const token = store.getters['auth/token']
      config.headers.Authorization = `JWT: ${token}`
    }
    return config
  })

  // If the user is authenticated, but is not refreshing in the browser means
  // that the refresh was done on the server side, so we need to manually start
  // the refreshing timeout here.
  if (
    store.getters['auth/isAuthenticated'] &&
    !store.getters['auth/isRefreshing'] &&
    process.browser
  ) {
    store.dispatch('auth/startRefreshTimeout')
  }
}
