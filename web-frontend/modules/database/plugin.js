import { DatabaseApplicationType } from '@baserow/modules/database/applicationTypes'
import {
  GridViewType,
  GalleryViewType,
  FormViewType,
} from '@baserow/modules/database/viewTypes'
import {
  TextFieldType,
  LongTextFieldType,
  URLFieldType,
  EmailFieldType,
  LinkRowFieldType,
  NumberFieldType,
  RatingFieldType,
  BooleanFieldType,
  DateFieldType,
  LastModifiedFieldType,
  FileFieldType,
  SingleSelectFieldType,
  MultipleSelectFieldType,
  PhoneNumberFieldType,
  CreatedOnFieldType,
  FormulaFieldType,
  LookupFieldType,
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
  LengthIsLowerThanViewFilterType,
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
  DateEqualsDayOfMonthViewFilterType,
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
import {
  ImageFilePreview,
  AudioFilePreview,
  VideoFilePreview,
  PDFBrowserFilePreview,
  GoogleDocFilePreview,
} from '@baserow/modules/database/filePreviewTypes'
import { APITokenSettingsType } from '@baserow/modules/database/settingsTypes'

import tableStore from '@baserow/modules/database/store/table'
import viewStore from '@baserow/modules/database/store/view'
import fieldStore from '@baserow/modules/database/store/field'
import gridStore from '@baserow/modules/database/store/view/grid'
import galleryStore from '@baserow/modules/database/store/view/gallery'
import formStore from '@baserow/modules/database/store/view/form'
import rowModal from '@baserow/modules/database/store/rowModal'

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
  BaserowLookup,
  BaserowSum,
  BaserowAvg,
  BaserowVariancePop,
  BaserowVarianceSample,
  BaserowStddevSample,
  BaserowStddevPop,
  BaserowJoin,
  BaserowCount,
  BaserowMin,
  BaserowMax,
  BaserowEvery,
  BaserowAny,
  BaserowWhenEmpty,
  BaserowSecond,
  BaserowYear,
  BaserowMonth,
  BaserowLeast,
  BaserowGreatest,
  BaserowRegexReplace,
  BaserowTrim,
  BaserowRight,
  BaserowLeft,
  BaserowContains,
  BaserowFilter,
} from '@baserow/modules/database/formula/functions'
import {
  BaserowFormulaArrayType,
  BaserowFormulaBooleanType,
  BaserowFormulaCharType,
  BaserowFormulaDateIntervalType,
  BaserowFormulaDateType,
  BaserowFormulaInvalidType,
  BaserowFormulaNumberType,
  BaserowFormulaSingleSelectType,
  BaserowFormulaSpecialType,
  BaserowFormulaTextType,
} from '@baserow/modules/database/formula/formulaTypes'

import en from '@baserow/modules/database/locales/en.json'
import fr from '@baserow/modules/database/locales/fr.json'

export default (context) => {
  const { store, app, isDev } = context

  // Allow locale file hot reloading in dev
  if (isDev && app.i18n) {
    const { i18n } = app
    i18n.mergeLocaleMessage('en', en)
    i18n.mergeLocaleMessage('fr', fr)
  }

  store.registerModule('table', tableStore)
  store.registerModule('view', viewStore)
  store.registerModule('field', fieldStore)
  store.registerModule('rowModal', rowModal)
  store.registerModule('page/view/grid', gridStore)
  store.registerModule('page/view/gallery', galleryStore)
  store.registerModule('page/view/form', formStore)
  store.registerModule('template/view/grid', gridStore)
  store.registerModule('template/view/gallery', galleryStore)
  store.registerModule('template/view/form', formStore)

  app.$registry.register('application', new DatabaseApplicationType(context))
  app.$registry.register('view', new GridViewType(context))
  app.$registry.register('view', new GalleryViewType(context))
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
  app.$registry.register(
    'viewFilter',
    new DateEqualsDayOfMonthViewFilterType(context)
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
  app.$registry.register(
    'viewFilter',
    new LengthIsLowerThanViewFilterType(context)
  )
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
  app.$registry.register('field', new RatingFieldType(context))
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
  app.$registry.register('field', new LookupFieldType(context))
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
  app.$registry.register('formula_function', new BaserowUpper(context))
  app.$registry.register('formula_function', new BaserowLower(context))
  app.$registry.register('formula_function', new BaserowConcat(context))
  app.$registry.register('formula_function', new BaserowToText(context))
  app.$registry.register('formula_function', new BaserowT(context))
  app.$registry.register('formula_function', new BaserowReplace(context))
  app.$registry.register('formula_function', new BaserowSearch(context))
  app.$registry.register('formula_function', new BaserowLength(context))
  app.$registry.register('formula_function', new BaserowReverse(context))
  // Number functions
  app.$registry.register('formula_function', new BaserowMultiply(context))
  app.$registry.register('formula_function', new BaserowDivide(context))
  app.$registry.register('formula_function', new BaserowToNumber(context))
  // Boolean functions
  app.$registry.register('formula_function', new BaserowIf(context))
  app.$registry.register('formula_function', new BaserowEqual(context))
  app.$registry.register('formula_function', new BaserowIsBlank(context))
  app.$registry.register('formula_function', new BaserowNot(context))
  app.$registry.register('formula_function', new BaserowNotEqual(context))
  app.$registry.register('formula_function', new BaserowGreaterThan(context))
  app.$registry.register(
    'formula_function',
    new BaserowGreaterThanOrEqual(context)
  )
  app.$registry.register('formula_function', new BaserowLessThan(context))
  app.$registry.register(
    'formula_function',
    new BaserowLessThanOrEqual(context)
  )
  app.$registry.register('formula_function', new BaserowAnd(context))
  app.$registry.register('formula_function', new BaserowOr(context))
  // Date functions
  app.$registry.register('formula_function', new BaserowDatetimeFormat(context))
  app.$registry.register('formula_function', new BaserowDay(context))
  app.$registry.register('formula_function', new BaserowToDate(context))
  app.$registry.register('formula_function', new BaserowDateDiff(context))
  // Date interval functions
  app.$registry.register('formula_function', new BaserowDateInterval(context))
  // Special functions
  app.$registry.register('formula_function', new BaserowAdd(context))
  app.$registry.register('formula_function', new BaserowMinus(context))
  app.$registry.register('formula_function', new BaserowField(context))
  app.$registry.register('formula_function', new BaserowLookup(context))
  app.$registry.register('formula_function', new BaserowRowId(context))
  app.$registry.register('formula_function', new BaserowContains(context))
  app.$registry.register('formula_function', new BaserowLeft(context))
  app.$registry.register('formula_function', new BaserowRight(context))
  app.$registry.register('formula_function', new BaserowTrim(context))
  app.$registry.register('formula_function', new BaserowRegexReplace(context))
  app.$registry.register('formula_function', new BaserowGreatest(context))
  app.$registry.register('formula_function', new BaserowLeast(context))
  app.$registry.register('formula_function', new BaserowMonth(context))
  app.$registry.register('formula_function', new BaserowYear(context))
  app.$registry.register('formula_function', new BaserowSecond(context))
  app.$registry.register('formula_function', new BaserowWhenEmpty(context))
  app.$registry.register('formula_function', new BaserowAny(context))
  app.$registry.register('formula_function', new BaserowEvery(context))
  app.$registry.register('formula_function', new BaserowMax(context))
  app.$registry.register('formula_function', new BaserowMin(context))
  app.$registry.register('formula_function', new BaserowCount(context))
  app.$registry.register('formula_function', new BaserowJoin(context))
  app.$registry.register('formula_function', new BaserowStddevPop(context))
  app.$registry.register('formula_function', new BaserowStddevSample(context))
  app.$registry.register('formula_function', new BaserowVarianceSample(context))
  app.$registry.register('formula_function', new BaserowVariancePop(context))
  app.$registry.register('formula_function', new BaserowAvg(context))
  app.$registry.register('formula_function', new BaserowSum(context))
  app.$registry.register('formula_function', new BaserowFilter(context))

  // Formula Types
  app.$registry.register('formula_type', new BaserowFormulaTextType(context))
  app.$registry.register('formula_type', new BaserowFormulaCharType(context))
  app.$registry.register('formula_type', new BaserowFormulaBooleanType(context))
  app.$registry.register('formula_type', new BaserowFormulaDateType(context))
  app.$registry.register(
    'formula_type',
    new BaserowFormulaDateIntervalType(context)
  )
  app.$registry.register('formula_type', new BaserowFormulaNumberType(context))
  app.$registry.register('formula_type', new BaserowFormulaArrayType(context))
  app.$registry.register('formula_type', new BaserowFormulaSpecialType(context))
  app.$registry.register('formula_type', new BaserowFormulaInvalidType(context))
  app.$registry.register(
    'formula_type',
    new BaserowFormulaSingleSelectType(context)
  )

  // File preview types
  app.$registry.register('preview', new ImageFilePreview(context))
  app.$registry.register('preview', new AudioFilePreview(context))
  app.$registry.register('preview', new VideoFilePreview(context))
  app.$registry.register('preview', new PDFBrowserFilePreview(context))
  app.$registry.register('preview', new GoogleDocFilePreview(context))

  registerRealtimeEvents(app.$realtime)
}
