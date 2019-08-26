import axios from 'axios'

export const client = axios.create({
  baseURL: process.env.baseUrl,
  withCredentials: false,
  headers: {
    Accept: 'application/json',
    'Content-Type': 'application/json'
  }
})
