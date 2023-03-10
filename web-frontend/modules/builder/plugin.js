import en from '@baserow/modules/builder/locales/en.json'
import fr from '@baserow/modules/builder/locales/fr.json'
import nl from '@baserow/modules/builder/locales/nl.json'
import de from '@baserow/modules/builder/locales/de.json'
import es from '@baserow/modules/builder/locales/es.json'
import it from '@baserow/modules/builder/locales/it.json'
import pl from '@baserow/modules/builder/locales/pl.json'
import {
  IntegrationsBuilderSettingsType,
  ThemeBuilderSettingsType,
} from '@baserow/modules/builder/builderSettingTypes'

import pageStore from '@baserow/modules/builder/store/page'
import { registerRealtimeEvents } from '@baserow/modules/builder/realtime'
import { DuplicatePageJobType } from '@baserow/modules/builder/jobTypes'
import { BuilderApplicationType } from '@baserow/modules/builder/applicationTypes'
import { PublicSiteErrorPageType } from '@baserow/modules/builder/errorPageTypes'

export default (context) => {
  const { store, app, isDev } = context

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

  registerRealtimeEvents(app.$realtime)

  store.registerModule('page', pageStore)

  app.$registry.registerNamespace('builderSettings')

  app.$registry.register('application', new BuilderApplicationType(context))
  app.$registry.register('job', new DuplicatePageJobType(context))

  app.$registry.register(
    'builderSettings',
    new IntegrationsBuilderSettingsType(context)
  )
  app.$registry.register(
    'builderSettings',
    new ThemeBuilderSettingsType(context)
  )

  app.$registry.register('errorPage', new PublicSiteErrorPageType(context))
}
