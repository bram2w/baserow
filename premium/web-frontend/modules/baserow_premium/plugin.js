import { PremiumPlugin } from '@baserow_premium/plugins'
import {
  JSONTableExporter,
  XMLTableExporter,
} from '@baserow_premium/tableExporterTypes'
import {
  DashboardType,
  GroupsAdminType,
  UsersAdminType,
  LicensesAdminType,
} from '@baserow_premium/adminTypes'
import rowCommentsStore from '@baserow_premium/store/row_comments'
import kanbanStore from '@baserow_premium/store/view/kanban'
import impersonatingStore from '@baserow_premium/store/impersonating'
import { PremiumDatabaseApplicationType } from '@baserow_premium/applicationTypes'
import { registerRealtimeEvents } from '@baserow_premium/realtime'
import { KanbanViewType } from '@baserow_premium/viewTypes'

import {
  LeftBorderColorViewDecoratorType,
  BackgroundColorViewDecoratorType,
} from '@baserow_premium/viewDecorators'

import {
  SingleSelectColorValueProviderType,
  ConditionalColorValueProviderType,
} from '@baserow_premium/decoratorValueProviders'
import { FormViewSurveyModeType } from '@baserow_premium/formViewModeTypes'

import en from '@baserow_premium/locales/en.json'
import fr from '@baserow_premium/locales/fr.json'
import nl from '@baserow_premium/locales/nl.json'
import de from '@baserow_premium/locales/de.json'
import es from '@baserow_premium/locales/es.json'
import it from '@baserow_premium/locales/it.json'
import pl from '@baserow_premium/locales/pl.json'
import { PremiumLicenseType } from '@baserow_premium/licenseTypes'

export default (context) => {
  const { store, app, isDev } = context

  app.$clientErrorMap.setError(
    'ERROR_FEATURE_NOT_AVAILABLE',
    'License required',
    'This functionality requires an active premium license. Please refresh the page.'
  )

  // Allow locale file hot reloading
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

  store.registerModule('row_comments', rowCommentsStore)
  store.registerModule('page/view/kanban', kanbanStore)
  store.registerModule('template/view/kanban', kanbanStore)
  store.registerModule('impersonating', impersonatingStore)

  app.$registry.register('plugin', new PremiumPlugin(context))
  app.$registry.register('admin', new DashboardType(context))
  app.$registry.register('admin', new UsersAdminType(context))
  app.$registry.register('admin', new GroupsAdminType(context))
  app.$registry.register('admin', new LicensesAdminType(context))
  app.$registry.register('exporter', new JSONTableExporter(context))
  app.$registry.register('exporter', new XMLTableExporter(context))
  app.$registry.register('view', new KanbanViewType(context))

  app.$registry.register(
    'viewDecorator',
    new LeftBorderColorViewDecoratorType(context)
  )
  app.$registry.register(
    'viewDecorator',
    new BackgroundColorViewDecoratorType(context)
  )

  app.$registry.register(
    'decoratorValueProvider',
    new SingleSelectColorValueProviderType(context)
  )
  app.$registry.register(
    'decoratorValueProvider',
    new ConditionalColorValueProviderType(context)
  )

  app.$registry.register('formViewMode', new FormViewSurveyModeType(context))

  app.$registry.register('license', new PremiumLicenseType(context))

  registerRealtimeEvents(app.$realtime)

  // Overwrite the existing database application type with the one customized for
  // premium use.
  app.$registry.register(
    'application',
    new PremiumDatabaseApplicationType(context)
  )
}
