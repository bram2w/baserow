import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import { GridViewType } from '@baserow/modules/database/viewTypes'
import {
  TextFieldType,
  LongTextFieldType,
  URLFieldType,
  EmailFieldType,
  LinkRowFieldType,
  NumberFieldType,
  BooleanFieldType,
  DateFieldType,
  FileFieldType,
  SingleSelectFieldType,
  PhoneNumberFieldType,
} from '@baserow/modules/database/fieldTypes'
import {
  EqualViewFilterType,
  NotEqualViewFilterType,
  DateEqualViewFilterType,
  DateNotEqualViewFilterType,
  ContainsViewFilterType,
  FilenameContainsViewFilterType,
  ContainsNotViewFilterType,
  HigherThanViewFilterType,
  LowerThanViewFilterType,
  SingleSelectEqualViewFilterType,
  SingleSelectNotEqualViewFilterType,
  BooleanViewFilterType,
  EmptyViewFilterType,
  NotEmptyViewFilterType,
  DateEqualsTodayViewFilterType,
  DateEqualsCurrentMonthViewFilterType,
  DateEqualsCurrentYearViewFilterType,
} from '@baserow/modules/database/viewFilters'
import {
  CSVImporterType,
  PasteImporterType,
  XMLImporterType,
  JSONImporterType,
} from '@baserow/modules/database/importerTypes'
import { APITokenSettingsType } from '@baserow/modules/database/settingsTypes'

import tableStore from '@baserow/modules/database/store/table'
import viewStore from '@baserow/modules/database/store/view'
import fieldStore from '@baserow/modules/database/store/field'
import gridStore from '@baserow/modules/database/store/view/grid'

import { registerRealtimeEvents } from '@baserow/modules/database/realtime'
import { CSVTableExporterType } from '@baserow/modules/database/exporterTypes'

export default ({ store, app }) => {
  store.registerModule('table', tableStore)
  store.registerModule('view', viewStore)
  store.registerModule('field', fieldStore)
  store.registerModule('page/view/grid', gridStore)
  store.registerModule('template/view/grid', gridStore)

  app.$registry.register('application', new DatabaseApplicationType())
  app.$registry.register('view', new GridViewType())
  app.$registry.register('viewFilter', new EqualViewFilterType())
  app.$registry.register('viewFilter', new NotEqualViewFilterType())
  app.$registry.register('viewFilter', new DateEqualViewFilterType())
  app.$registry.register('viewFilter', new DateNotEqualViewFilterType())
  app.$registry.register('viewFilter', new DateEqualsTodayViewFilterType())
  app.$registry.register(
    'viewFilter',
    new DateEqualsCurrentMonthViewFilterType()
  )
  app.$registry.register(
    'viewFilter',
    new DateEqualsCurrentYearViewFilterType()
  )
  app.$registry.register('viewFilter', new ContainsViewFilterType())
  app.$registry.register('viewFilter', new FilenameContainsViewFilterType())
  app.$registry.register('viewFilter', new ContainsNotViewFilterType())
  app.$registry.register('viewFilter', new HigherThanViewFilterType())
  app.$registry.register('viewFilter', new LowerThanViewFilterType())
  app.$registry.register('viewFilter', new SingleSelectEqualViewFilterType())
  app.$registry.register('viewFilter', new SingleSelectNotEqualViewFilterType())
  app.$registry.register('viewFilter', new BooleanViewFilterType())
  app.$registry.register('viewFilter', new EmptyViewFilterType())
  app.$registry.register('viewFilter', new NotEmptyViewFilterType())
  app.$registry.register('field', new TextFieldType())
  app.$registry.register('field', new LongTextFieldType())
  app.$registry.register('field', new LinkRowFieldType())
  app.$registry.register('field', new NumberFieldType())
  app.$registry.register('field', new BooleanFieldType())
  app.$registry.register('field', new DateFieldType())
  app.$registry.register('field', new URLFieldType())
  app.$registry.register('field', new EmailFieldType())
  app.$registry.register('field', new FileFieldType())
  app.$registry.register('field', new SingleSelectFieldType())
  app.$registry.register('field', new PhoneNumberFieldType())
  app.$registry.register('importer', new CSVImporterType())
  app.$registry.register('importer', new PasteImporterType())
  app.$registry.register('importer', new XMLImporterType())
  app.$registry.register('importer', new JSONImporterType())
  app.$registry.register('settings', new APITokenSettingsType())
  app.$registry.register('exporter', new CSVTableExporterType())

  registerRealtimeEvents(app.$realtime)
}
