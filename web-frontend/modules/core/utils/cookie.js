import { isSecureURL } from './string'

export const userSourceCookieTokenName = 'user_source_token'
export const refreshTokenMaxAge = 60 * 60 * 24 * 7

export const getCookieName = (config, key) => {
  return `${config.public.baserowFrontendCookiePrefix || ''}${key}`
}

export const getTokenCookieOptions = (config, sameSite = null) => ({
  path: '/',
  maxAge: refreshTokenMaxAge,
  sameSite: sameSite || config.public.baserowFrontendSameSiteCookie,
  secure: isSecureURL(config.public.publicWebFrontendUrl),
})
