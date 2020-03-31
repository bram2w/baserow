import axios from 'axios'

const url =
  process.client && process.env.publicBaseUrl
    ? process.env.publicBaseUrl
    : process.env.baseUrl

export const client = axios.create({
  baseURL: url,
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  },
})
