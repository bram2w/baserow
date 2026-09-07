import { defineNuxtPlugin } from '#app'
import { clearPendingLogin } from '@baserow/modules/builder/utils/pendingLogin'

export default defineNuxtPlugin(() => {
  // Provider errors render Nuxt's error page without mounting PublicPageContent.
  // Discard the initiating event there as well, before a later login can occur.
  const query = new URLSearchParams(window.location.search)
  if ([...query.keys()].some((key) => /^(saml|oidc)_error__\d+$/.test(key))) {
    clearPendingLogin()
  }
})
