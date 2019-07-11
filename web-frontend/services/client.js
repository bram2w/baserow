import axios from 'axios'

export const client = axios.create({
  baseURL: process.env.baseUrl,
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})

client.interceptors.response.use(
  response => {
    return response
  },
  error => {
    error.responseError = undefined
    error.responseDetail = undefined

    if (
      error.response &&
      'error' in error.response.data &&
      'detail' in error.response.data
    ) {
      error.responseError = error.response.data.error
      error.responseDetail = error.response.data.detail
    }

    return Promise.reject(error)
  }
)
