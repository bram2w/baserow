import axios from 'axios'
import { baserowConfig } from './playwright.config'
import { User } from './fixtures/user'

export function getClient(user?: User) {
  const baseURL = `${baserowConfig.PUBLIC_BACKEND_URL}/api/`
  const instance = axios.create({
    baseURL,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'Accept-Encoding': 'gzip, compress, deflate, br',
    },
  })
  if (user !== undefined) {
    instance.defaults.headers.Authorization = `JWT ${user.accessToken}`
  }

// Add a response interceptor
    instance.interceptors.response.use(function (response) {
        // Do something with response data
        return response;
    }, function (error) {
        if (error.response) {
            console.error('API response error:', JSON.stringify(error.response.data));
        }
        // Do something with response error
        return Promise.reject(error);
    });

    return instance
}
