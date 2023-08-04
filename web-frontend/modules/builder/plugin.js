import en from '@baserow/modules/builder/locales/en.json'
import fr from '@baserow/modules/builder/locales/fr.json'
import nl from '@baserow/modules/builder/locales/nl.json'
import de from '@baserow/modules/builder/locales/de.json'
import es from '@baserow/modules/builder/locales/es.json'
import it from '@baserow/modules/builder/locales/it.json'
import pl from '@baserow/modules/builder/locales/pl.json'
import {
  DomainsBuilderSettingsType,
  IntegrationsBuilderSettingsType,
  ThemeBuilderSettingsType,
} from '@baserow/modules/builder/builderSettingTypes'

import pageStore from '@baserow/modules/builder/store/page'
import elementStore from '@baserow/modules/builder/store/element'
import domainStore from '@baserow/modules/builder/store/domain'
import publicBuilderStore from '@baserow/modules/builder/store/publicBuilder'
import dataSourceStore from '@baserow/modules/builder/store/dataSource'
import pageParameterStore from '@baserow/modules/builder/store/pageParameter'
import dataSourceContentStore from '@baserow/modules/builder/store/dataSourceContent'

import { registerRealtimeEvents } from '@baserow/modules/builder/realtime'
import {
  HeadingElementType,
  ImageElementType,
  ParagraphElementType,
  LinkElementType,
  InputTextElementType,
} from '@baserow/modules/builder/elementTypes'
import {
  DesktopDeviceType,
  SmartphoneDeviceType,
  TabletDeviceType,
} from '@baserow/modules/builder/deviceTypes'
import { DuplicatePageJobType } from '@baserow/modules/builder/jobTypes'
import { BuilderApplicationType } from '@baserow/modules/builder/applicationTypes'
import { PublicSiteErrorPageType } from '@baserow/modules/builder/errorPageTypes'
import {
  DataSourcesPageHeaderItemType,
  ElementsPageHeaderItemType,
  SettingsPageHeaderItemType,
  VariablesPageHeaderItemType,
} from '@baserow/modules/builder/pageHeaderItemTypes'
import {
  EventsPageSidePanelType,
  GeneralPageSidePanelType,
  VisibilityPageSidePanelType,
  StylePageSidePanelType,
} from '@baserow/modules/builder/pageSidePanelTypes'
import { CustomDomainType } from '@baserow/modules/builder/domainTypes'
import { PagePageSettingsType } from '@baserow/modules/builder/pageSettingsTypes'
import {
  TextPathParamType,
  NumericPathParamType,
} from '@baserow/modules/builder/pathParamTypes'

import {
  PreviewPageActionType,
  PublishPageActionType,
} from '@baserow/modules/builder/pageActionTypes'

import {
  PageParameterDataProviderType,
  DataSourceDataProviderType,
} from '@baserow/modules/builder/dataProviderTypes'

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
  store.registerModule('element', elementStore)
  store.registerModule('domain', domainStore)
  store.registerModule('publicBuilder', publicBuilderStore)
  store.registerModule('dataSource', dataSourceStore)
  store.registerModule('pageParameter', pageParameterStore)
  store.registerModule('dataSourceContent', dataSourceContentStore)

  app.$registry.registerNamespace('builderSettings')
  app.$registry.registerNamespace('element')
  app.$registry.registerNamespace('device')
  app.$registry.registerNamespace('pageHeaderItem')
  app.$registry.registerNamespace('domain')
  app.$registry.registerNamespace('pageSettings')
  app.$registry.registerNamespace('pathParamType')
  app.$registry.registerNamespace('builderDataProvider')

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
  app.$registry.register(
    'builderSettings',
    new DomainsBuilderSettingsType(context)
  )

  app.$registry.register('errorPage', new PublicSiteErrorPageType(context))

  app.$registry.register('element', new HeadingElementType(context))
  app.$registry.register('element', new ParagraphElementType(context))
  app.$registry.register('element', new LinkElementType(context))
  app.$registry.register('element', new ImageElementType(context))
  app.$registry.register('element', new InputTextElementType(context))

  app.$registry.register('device', new DesktopDeviceType(context))
  app.$registry.register('device', new TabletDeviceType(context))
  app.$registry.register('device', new SmartphoneDeviceType(context))

  app.$registry.register(
    'pageHeaderItem',
    new ElementsPageHeaderItemType(context)
  )
  app.$registry.register(
    'pageHeaderItem',
    new DataSourcesPageHeaderItemType(context)
  )
  app.$registry.register(
    'pageHeaderItem',
    new VariablesPageHeaderItemType(context)
  )
  app.$registry.register(
    'pageHeaderItem',
    new SettingsPageHeaderItemType(context)
  )
  app.$registry.register('pageSidePanel', new GeneralPageSidePanelType(context))
  app.$registry.register('pageSidePanel', new StylePageSidePanelType(context))
  app.$registry.register(
    'pageSidePanel',
    new VisibilityPageSidePanelType(context)
  )
  app.$registry.register('pageSidePanel', new EventsPageSidePanelType(context))

  app.$registry.register('domain', new CustomDomainType(context))

  app.$registry.register('pageSettings', new PagePageSettingsType(context))

  app.$registry.register('pathParamType', new TextPathParamType(context))
  app.$registry.register('pathParamType', new NumericPathParamType(context))

  app.$registry.register('pageAction', new PublishPageActionType(context))
  app.$registry.register('pageAction', new PreviewPageActionType(context))

  app.$registry.register(
    'builderDataProvider',
    new DataSourceDataProviderType(context)
  )
  app.$registry.register(
    'builderDataProvider',
    new PageParameterDataProviderType(context)
  )
}
