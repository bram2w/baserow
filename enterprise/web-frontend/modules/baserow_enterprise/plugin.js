import { registerRealtimeEvents } from '@baserow_enterprise/realtime'
import { AuthProvidersType } from '@baserow_enterprise/adminTypes'
import { SamlAuthProviderType } from '@baserow_enterprise/authProviderTypes'
import authProviderAdminStore from '@baserow_enterprise/store/authProviderAdmin'

import en from '@baserow_enterprise/locales/en.json'
import fr from '@baserow_enterprise/locales/fr.json'
import nl from '@baserow_enterprise/locales/nl.json'
import de from '@baserow_enterprise/locales/de.json'
import es from '@baserow_enterprise/locales/es.json'
import it from '@baserow_enterprise/locales/it.json'
import { EnterpriseLicenseType } from '@baserow_enterprise/licenseTypes'

export default (context) => {
  const { app, isDev, store } = context

  // Allow locale file hot reloading
  if (isDev && app.i18n) {
    const { i18n } = app
    i18n.mergeLocaleMessage('en', en)
    i18n.mergeLocaleMessage('fr', fr)
    i18n.mergeLocaleMessage('nl', nl)
    i18n.mergeLocaleMessage('de', de)
    i18n.mergeLocaleMessage('es', es)
    i18n.mergeLocaleMessage('it', it)
  }

  store.registerModule('authProviderAdmin', authProviderAdminStore)

  app.$registry.register('admin', new AuthProvidersType(context))
  app.$registry.register('authProvider', new SamlAuthProviderType(context))

  registerRealtimeEvents(app.$realtime)

  app.$registry.register('license', new EnterpriseLicenseType(context))
}
