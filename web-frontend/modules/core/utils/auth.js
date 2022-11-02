import { isSecureURL } from '@baserow/modules/core/utils/string'
import jwtDecode from 'jwt-decode'

const cookieTokenName = 'jwt_token'

export const setToken = (token, { $cookies, $env }, key = cookieTokenName) => {
  if (process.SERVER_BUILD) return
  const secure = isSecureURL($env.PUBLIC_WEB_FRONTEND_URL)
  $cookies.set(key, token, {
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
    sameSite: 'lax',
    secure,
  })
}

export const unsetToken = ({ $cookies }, key = cookieTokenName) => {
  if (process.SERVER_BUILD) return
  $cookies.remove(key)
}

export const getToken = ({ $cookies }, key = cookieTokenName) => {
  return $cookies.get(key)
}

export const getTokenIfEnoughTimeLeft = (
  { $cookies },
  key = cookieTokenName
) => {
  const token = getToken({ $cookies }, key)
  if (!token) return null

  const decodedToken = jwtDecode(token)
  const now = Math.ceil(new Date().getTime() / 1000)
  // Return the token if it is still valid for more of the 10% of the lifespan.
  if ((decodedToken.exp - now) / (decodedToken.exp - decodedToken.iat) > 0.1) {
    return token
  }
}
