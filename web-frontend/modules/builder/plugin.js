import { BuilderApplicationType } from '@baserow/modules/builder/applicationTypes'
import en from '@baserow/modules/builder/locales/en.json'
import fr from '@baserow/modules/builder/locales/fr.json'
import nl from '@baserow/modules/builder/locales/nl.json'
import de from '@baserow/modules/builder/locales/de.json'
import es from '@baserow/modules/builder/locales/es.json'
import it from '@baserow/modules/builder/locales/it.json'
import pl from '@baserow/modules/builder/locales/pl.json'

export default (context) => {
  const { app, isDev } = context

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

  app.$registry.register('application', new BuilderApplicationType(context))
}
