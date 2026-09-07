import {
  defineEventHandler,
  getRequestURL,
  sendRedirect,
  setCookie,
  setResponseHeader,
} from 'h3'
import { useRuntimeConfig } from 'nitropack/runtime'
import {
  getCookieName,
  getTokenCookieOptions,
  userSourceCookieTokenName,
} from '../../../core/utils/cookie'
import {
  consumeUserSourceCallback,
  getLoginCompletionCookieName,
} from '../../../core/utils/userSourceCallback'

// Consume the backend callback before Nuxt renders the public page or its payload.
export default defineEventHandler((event) => {
  const callback = consumeUserSourceCallback(getRequestURL(event))
  if (!callback) {
    return
  }

  const config = useRuntimeConfig(event)
  if (callback.token) {
    setCookie(
      event,
      getCookieName(config, userSourceCookieTokenName),
      callback.token,
      getTokenCookieOptions(config, 'lax')
    )
  }
  if (callback.token && callback.attemptId) {
    setCookie(
      event,
      getCookieName(config, getLoginCompletionCookieName(callback.attemptId)),
      '1',
      {
        ...getTokenCookieOptions(config, 'lax'),
        maxAge: 60,
      }
    )
  }
  setResponseHeader(event, 'Cache-Control', 'no-store')
  setResponseHeader(event, 'Referrer-Policy', 'no-referrer')
  return sendRedirect(event, callback.url.pathname + callback.url.search, 303)
})
