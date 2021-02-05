import { isSecureURL } from '@baserow/modules/core/utils/string'

const cookieTokenName = 'jwt_token'

export const setToken = (token, { $cookies, $env }) => {
  if (process.SERVER_BUILD) return
  const secure = isSecureURL($env.PUBLIC_WEB_FRONTEND_URL)
  $cookies.set(cookieTokenName, token, {
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
    sameSite: 'lax',
    secure,
  })
}

export const unsetToken = ({ $cookies }) => {
  if (process.SERVER_BUILD) return
  $cookies.remove(cookieTokenName)
}

export const getToken = ({ $cookies }) => {
  return $cookies.get(cookieTokenName)
}
