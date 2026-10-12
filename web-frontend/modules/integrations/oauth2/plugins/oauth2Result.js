import { defineNuxtPlugin } from '#imports'
import {
  clearOAuth2Flow,
  getOAuth2Flow,
} from '@baserow/modules/integrations/oauth2/utils/flow'

const PARAMS = ['oauth2_status', 'oauth2_error', 'oauth2_integration']

/**
 * The OAuth2 completion page sends the browser back to the page the
 * connection was started from with the outcome in the query string. Shown
 * once as a toast, then removed from the URL so a reload does not repeat it.
 * Only shown when this tab started a flow, so a crafted link cannot put an
 * arbitrary message in front of the user.
 */
export default defineNuxtPlugin((nuxtApp) => {
  if (import.meta.server) {
    return
  }
  nuxtApp.hook('app:mounted', () => {
    const url = new URL(window.location.href)
    const status = url.searchParams.get('oauth2_status')
    if (!status) {
      return
    }
    const error = url.searchParams.get('oauth2_error')
    PARAMS.forEach((param) => url.searchParams.delete(param))
    window.history.replaceState(window.history.state, '', url.toString())
    if (!getOAuth2Flow()) {
      return
    }
    clearOAuth2Flow()

    const store = nuxtApp.$store
    const i18n = nuxtApp.$i18n
    if (status === 'success') {
      store.dispatch('toast/success', {
        title: i18n.t('oauth2Result.successTitle'),
        message: i18n.t('oauth2Result.successMessage'),
      })
    } else {
      store.dispatch('toast/error', {
        title: i18n.t('oauth2Result.errorTitle'),
        message: error || i18n.t('oauth2Result.errorMessage'),
      })
    }
  })
})
