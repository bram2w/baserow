const cookieTokenName = 'jwt_token'

export const setToken = (token, cookie) => {
  if (process.SERVER_BUILD) return
  cookie.set(cookieTokenName, token, {
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
  })
}

export const unsetToken = (cookie) => {
  if (process.SERVER_BUILD) return
  cookie.remove(cookieTokenName)
}

export const getToken = (cookie) => {
  return cookie.get(cookieTokenName)
}
