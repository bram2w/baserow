import { client } from '@/services/client'

export default function({ store }) {
  // Create a request interceptor to add the authorization token to every
  // request if the user is authenticated.
  client.interceptors.request.use(config => {
    if (store.getters['auth/isAuthenticated']) {
      const token = store.getters['auth/token']
      config.headers.Authorization = `JWT ${token}`
    }
    return config
  })

  // Create a response interceptor to add more detail tot the error message
  // and to create a notification when there is a network error.
  client.interceptors.response.use(
    response => {
      return response
    },
    error => {
      error.responseError = undefined
      error.responseDetail = undefined

      // Add the error message in the response to the error object.
      if (
        error.response &&
        'error' in error.response.data &&
        'detail' in error.response.data
      ) {
        error.responseError = error.response.data.error
        error.responseDetail = error.response.data.detail
      }

      // Network error, the server could not reached
      if (!error.response) {
        store.dispatch('notification/error', {
          title: 'Network error',
          message: 'Could not connect to the API server.'
        })
      }

      return Promise.reject(error)
    }
  )
}
