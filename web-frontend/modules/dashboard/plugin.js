import en from '@baserow/modules/dashboard/locales/en.json'
import fr from '@baserow/modules/dashboard/locales/fr.json'
import nl from '@baserow/modules/dashboard/locales/nl.json'
import de from '@baserow/modules/dashboard/locales/de.json'
import es from '@baserow/modules/dashboard/locales/es.json'
import it from '@baserow/modules/dashboard/locales/it.json'
import pl from '@baserow/modules/dashboard/locales/pl.json'

import { DashboardApplicationType } from '@baserow/modules/dashboard/applicationTypes'
import dashboardApplicationStore from '@baserow/modules/dashboard/store/dashboardApplication'
import { FF_DASHBOARDS } from '@baserow/modules/core/plugins/featureFlags'

export default (context) => {
  const { app, isDev, store } = context

  // Allow locale file hot reloading in dev
  if (isDev && app.i18n) {
    const { i18n } = app
    i18n.mergeLocaleMessage('en', en)
    i18n.mergeLocaleMessage('fr', fr)
    i18n.mergeLocaleMessage('nl', nl)
    i18n.mergeLocaleMessage('de', de)
    i18n.mergeLocaleMessage('es', es)
    i18n.mergeLocaleMessage('it', it)
    i18n.mergeLocaleMessage('pl', pl)
  }

  store.registerModule('dashboardApplication', dashboardApplicationStore)

  if (app.$featureFlagIsEnabled(FF_DASHBOARDS)) {
    app.$registry.register('application', new DashboardApplicationType(context))
  }
}
