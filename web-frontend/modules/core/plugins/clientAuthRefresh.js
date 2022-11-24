export function makeRefreshAuthInterceptor(
  client,
  refreshAuthFunction,
  shouldInterceptRequest,
  shouldInterceptResponse,
  retryRequestFunction = null
) {
  /**
   * This interceptor adds the ability to automatically refresh the access token
   * when needed. Intercept all the responses where
   * `shouldInterceptResponse(error)` returns true as well as any requests where
   * `shouldInterceptRequest(config)` returns true. Then, it refreshes the auth
   * token before retrying the failed requests or continue with the intercepted
   * ones. Set `config.skipAuthRefresh = true` in the axios request to skip this
   * interceptor.
   */

  // create the promise once and use it for all concurrent requests
  let refreshPromise
  const getRefreshAuthPromise = () => {
    if (refreshPromise === undefined) {
      refreshPromise = refreshAuthFunction()
      refreshPromise.finally(() => (refreshPromise = undefined))
    }
    return refreshPromise
  }

  // Refresh the auth token if needed before sending the initial request.
  client.interceptors.request.use((config) => {
    if (
      (shouldInterceptRequest(config) || refreshPromise) &&
      !config.skipAuthRefresh
    ) {
      return getRefreshAuthPromise().then(() => config)
    }
    return config
  })

  const retry = retryRequestFunction || ((config) => client(config))

  // Refresh the auth token and retry the failed request if needed.
  return (error) => {
    const config = error.config
    if (shouldInterceptResponse(error) && !config.skipAuthRefresh) {
      config.skipAuthRefresh = true
      return getRefreshAuthPromise().then(() => retry(config))
    }
    return Promise.reject(error)
  }
}
