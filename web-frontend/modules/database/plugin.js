import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import { GridViewType, FormViewType } from '@baserow/modules/database/viewTypes'
import {
  TextFieldType,
  LongTextFieldType,
  URLFieldType,
  EmailFieldType,
  LinkRowFieldType,
  NumberFieldType,
  BooleanFieldType,
  DateFieldType,
  LastModifiedFieldType,
  FileFieldType,
  SingleSelectFieldType,
  MultipleSelectFieldType,
  PhoneNumberFieldType,
  CreatedOnFieldType,
  FormulaFieldType,
} from '@baserow/modules/database/fieldTypes'
import {
  EqualViewFilterType,
  NotEqualViewFilterType,
  DateEqualViewFilterType,
  DateNotEqualViewFilterType,
  ContainsViewFilterType,
  FilenameContainsViewFilterType,
  HasFileTypeViewFilterType,
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
  DateBeforeViewFilterType,
  DateAfterViewFilterType,
  LinkRowHasFilterType,
  LinkRowHasNotFilterType,
  MultipleSelectHasFilterType,
  MultipleSelectHasNotFilterType,
} from '@baserow/modules/database/viewFilters'
import {
  CSVImporterType,
  PasteImporterType,
  XMLImporterType,
  JSONImporterType,
} from '@baserow/modules/database/importerTypes'
import {
  RowCreatedWebhookEventType,
  RowUpdatedWebhookEventType,
  RowDeletedWebhookEventType,
} from '@baserow/modules/database/webhookEventTypes'
import { APITokenSettingsType } from '@baserow/modules/database/settingsTypes'

import tableStore from '@baserow/modules/database/store/table'
import viewStore from '@baserow/modules/database/store/view'
import fieldStore from '@baserow/modules/database/store/field'
import gridStore from '@baserow/modules/database/store/view/grid'
import formStore from '@baserow/modules/database/store/view/form'

import { registerRealtimeEvents } from '@baserow/modules/database/realtime'
import { CSVTableExporterType } from '@baserow/modules/database/exporterTypes'
import {
  BaserowAdd,
  BaserowAnd,
  BaserowConcat,
  BaserowDateDiff,
  BaserowDateInterval,
  BaserowDatetimeFormat,
  BaserowDay,
  BaserowDivide,
  BaserowEqual,
  BaserowField,
  BaserowSearch,
  BaserowGreaterThan,
  BaserowGreaterThanOrEqual,
  BaserowIf,
  BaserowIsBlank,
  BaserowLessThan,
  BaserowLessThanOrEqual,
  BaserowLower,
  BaserowMinus,
  BaserowMultiply,
  BaserowNot,
  BaserowOr,
  BaserowReplace,
  BaserowRowId,
  BaserowT,
  BaserowToDate,
  BaserowToNumber,
  BaserowToText,
  BaserowUpper,
  BaserowReverse,
  BaserowLength,
  BaserowNotEqual,
} from '@baserow/modules/database/formula/functions'

export default (context) => {
  const { store, app } = context
  store.registerModule('table', tableStore)
  store.registerModule('view', viewStore)
  store.registerModule('field', fieldStore)
  store.registerModule('page/view/grid', gridStore)
  store.registerModule('page/view/form', formStore)
  store.registerModule('template/view/grid', gridStore)
  store.registerModule('template/view/form', formStore)

  app.$registry.register('application', new DatabaseApplicationType(context))
  app.$registry.register('view', new GridViewType(context))
  app.$registry.register('view', new FormViewType(context))
  app.$registry.register('viewFilter', new EqualViewFilterType(context))
  app.$registry.register('viewFilter', new NotEqualViewFilterType(context))
  app.$registry.register('viewFilter', new DateEqualViewFilterType(context))
  app.$registry.register('viewFilter', new DateNotEqualViewFilterType(context))
  app.$registry.register(
    'viewFilter',
    new DateEqualsTodayViewFilterType(context)
  )
  app.$registry.register(
    'viewFilter',
    new DateEqualsCurrentMonthViewFilterType(context)
  )
  app.$registry.register(
    'viewFilter',
    new DateEqualsCurrentYearViewFilterType(context)
  )
  app.$registry.register('viewFilter', new DateBeforeViewFilterType(context))
  app.$registry.register('viewFilter', new DateAfterViewFilterType(context))
  app.$registry.register('viewFilter', new ContainsViewFilterType(context))
  app.$registry.register(
    'viewFilter',
    new FilenameContainsViewFilterType(context)
  )
  app.$registry.register('viewFilter', new HasFileTypeViewFilterType(context))
  app.$registry.register('viewFilter', new ContainsNotViewFilterType(context))
  app.$registry.register('viewFilter', new HigherThanViewFilterType(context))
  app.$registry.register('viewFilter', new LowerThanViewFilterType(context))
  app.$registry.register(
    'viewFilter',
    new SingleSelectEqualViewFilterType(context)
  )
  app.$registry.register(
    'viewFilter',
    new SingleSelectNotEqualViewFilterType(context)
  )
  app.$registry.register('viewFilter', new BooleanViewFilterType(context))
  app.$registry.register('viewFilter', new LinkRowHasFilterType(context))
  app.$registry.register('viewFilter', new LinkRowHasNotFilterType(context))
  app.$registry.register('viewFilter', new MultipleSelectHasFilterType(context))
  app.$registry.register(
    'viewFilter',
    new MultipleSelectHasNotFilterType(context)
  )
  app.$registry.register('viewFilter', new EmptyViewFilterType(context))
  app.$registry.register('viewFilter', new NotEmptyViewFilterType(context))
  app.$registry.register('field', new TextFieldType(context))
  app.$registry.register('field', new LongTextFieldType(context))
  app.$registry.register('field', new LinkRowFieldType(context))
  app.$registry.register('field', new NumberFieldType(context))
  app.$registry.register('field', new BooleanFieldType(context))
  app.$registry.register('field', new DateFieldType(context))
  app.$registry.register('field', new LastModifiedFieldType(context))
  app.$registry.register('field', new CreatedOnFieldType(context))
  app.$registry.register('field', new URLFieldType(context))
  app.$registry.register('field', new EmailFieldType(context))
  app.$registry.register('field', new FileFieldType(context))
  app.$registry.register('field', new SingleSelectFieldType(context))
  app.$registry.register('field', new MultipleSelectFieldType(context))
  app.$registry.register('field', new PhoneNumberFieldType(context))
  app.$registry.register('field', new FormulaFieldType(context))
  app.$registry.register('importer', new CSVImporterType(context))
  app.$registry.register('importer', new PasteImporterType(context))
  app.$registry.register('importer', new XMLImporterType(context))
  app.$registry.register('importer', new JSONImporterType(context))
  app.$registry.register('settings', new APITokenSettingsType(context))
  app.$registry.register('exporter', new CSVTableExporterType(context))
  app.$registry.register(
    'webhookEvent',
    new RowCreatedWebhookEventType(context)
  )
  app.$registry.register(
    'webhookEvent',
    new RowUpdatedWebhookEventType(context)
  )
  app.$registry.register(
    'webhookEvent',
    new RowDeletedWebhookEventType(context)
  )

  // Text functions
  app.$registry.register('formula_function', new BaserowUpper())
  app.$registry.register('formula_function', new BaserowLower())
  app.$registry.register('formula_function', new BaserowConcat())
  app.$registry.register('formula_function', new BaserowToText())
  app.$registry.register('formula_function', new BaserowT())
  app.$registry.register('formula_function', new BaserowReplace())
  app.$registry.register('formula_function', new BaserowSearch())
  app.$registry.register('formula_function', new BaserowLength())
  app.$registry.register('formula_function', new BaserowReverse())
  // Number functions
  app.$registry.register('formula_function', new BaserowMultiply())
  app.$registry.register('formula_function', new BaserowDivide())
  app.$registry.register('formula_function', new BaserowToNumber())
  // Boolean functions
  app.$registry.register('formula_function', new BaserowIf())
  app.$registry.register('formula_function', new BaserowEqual())
  app.$registry.register('formula_function', new BaserowIsBlank())
  app.$registry.register('formula_function', new BaserowNot())
  app.$registry.register('formula_function', new BaserowNotEqual())
  app.$registry.register('formula_function', new BaserowGreaterThan())
  app.$registry.register('formula_function', new BaserowGreaterThanOrEqual())
  app.$registry.register('formula_function', new BaserowLessThan())
  app.$registry.register('formula_function', new BaserowLessThanOrEqual())
  app.$registry.register('formula_function', new BaserowAnd())
  app.$registry.register('formula_function', new BaserowOr())
  // Date functions
  app.$registry.register('formula_function', new BaserowDatetimeFormat())
  app.$registry.register('formula_function', new BaserowDay())
  app.$registry.register('formula_function', new BaserowToDate())
  app.$registry.register('formula_function', new BaserowDateDiff())
  // Date interval functions
  app.$registry.register('formula_function', new BaserowDateInterval())
  // Special functions
  app.$registry.register('formula_function', new BaserowAdd())
  app.$registry.register('formula_function', new BaserowMinus())
  app.$registry.register('formula_function', new BaserowField())
  app.$registry.register('formula_function', new BaserowRowId())

  registerRealtimeEvents(app.$realtime)
}
