import { isSecureURL } from '@baserow/modules/core/utils/string'
import jwtDecode from 'jwt-decode'

const cookieTokenName = 'jwt_token'
export const userSourceCookieTokenName = 'user_source_token'

export const setToken = (
  { $config, $cookies },
  token,
  key = cookieTokenName,
  configuration = { sameSite: null }
) => {
  if (process.SERVER_BUILD) return
  const secure = isSecureURL($config.PUBLIC_WEB_FRONTEND_URL)
  $cookies.set(key, token, {
    path: '/',
    maxAge: 60 * 60 * 24 * 7,
    sameSite:
      configuration.sameSite || $config.BASEROW_FRONTEND_SAME_SITE_COOKIE,
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
  const now = Math.ceil(new Date().getTime() / 1000)

  let data
  try {
    data = jwtDecode(token)
  } catch (error) {
    return null
  }
  // Return the token if it is still valid for more of the 10% of the lifespan.
  return data && (data.exp - now) / (data.exp - data.iat) > 0.1 ? token : null
}

export const logoutAndRedirectToLogin = (
  router,
  store,
  showSessionExpiredToast = false,
  showPasswordChangedToast = false,
  invalidateToken = false
) => {
  if (showPasswordChangedToast) {
    store.dispatch('auth/forceLogoff')
  } else {
    store.dispatch('auth/logoff', { invalidateToken })
  }
  router.push({ name: 'login', query: { noredirect: null } }, () => {
    if (showSessionExpiredToast) {
      store.dispatch('toast/setUserSessionExpired', true)
    } else if (showPasswordChangedToast) {
      store.dispatch('toast/setUserPasswordChanged', true)
    }
    store.dispatch('auth/clearAllStoreUserData')
  })
}
