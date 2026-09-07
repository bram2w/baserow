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
import { consumeUserSourceCallback } from '../../../core/utils/userSourceCallback'

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
  setResponseHeader(event, 'Cache-Control', 'no-store')
  setResponseHeader(event, 'Referrer-Policy', 'no-referrer')
  return sendRedirect(event, callback.url.pathname + callback.url.search, 303)
})
