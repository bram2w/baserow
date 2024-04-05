import { FieldType } from '@baserow/modules/database/fieldTypes'
import RowHistoryFieldText from '@baserow/modules/database/components/row/RowHistoryFieldText'
import RowCardFieldText from '@baserow/modules/database/components/card/RowCardFieldText'
import { collatedStringCompare } from '@baserow/modules/core/utils/string'
import {
  genericContainsFilter,
  genericContainsWordFilter,
} from '@baserow/modules/database/utils/fieldFilters'

import GridViewFieldAI from '@baserow_premium/components/views/grid/fields/GridViewFieldAI'
import FunctionalGridViewFieldAI from '@baserow_premium/components/views/grid/fields/FunctionalGridViewFieldAI'
import RowEditFieldAI from '@baserow_premium/components/row/RowEditFieldAI'
import FieldAISubForm from '@baserow_premium/components/field/FieldAISubForm'
import GridViewFieldAIGenerateValuesContextItem from '@baserow_premium/components/views/grid/fields/GridViewFieldAIGenerateValuesContextItem'

export class AIFieldType extends FieldType {
  static getType() {
    return 'ai'
  }

  getIconClass() {
    return 'iconoir-magic-wand'
  }

  getName() {
    const { i18n } = this.app
    return i18n.t('premiumFieldType.ai')
  }

  getGridViewFieldComponent() {
    return GridViewFieldAI
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldAI
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldAI
  }

  getCardComponent() {
    return RowCardFieldText
  }

  getRowHistoryEntryComponent() {
    return RowHistoryFieldText
  }

  getFormComponent() {
    return FieldAISubForm
  }

  getFormViewFieldComponents(field) {
    return {}
  }

  getEmptyValue(field) {
    return null
  }

  getSort(name, order) {
    return (a, b) => {
      const stringA = a[name] === null ? '' : '' + a[name]
      const stringB = b[name] === null ? '' : '' + b[name]

      return collatedStringCompare(stringA, stringB, order)
    }
  }

  getDocsDataType(field) {
    return 'string'
  }

  getDocsDescription(field) {
    return '@TODO'
  }

  getDocsRequestExample(field) {
    return 'string'
  }

  getContainsFilterFunction() {
    return genericContainsFilter
  }

  getContainsWordFilterFunction(field) {
    return genericContainsWordFilter
  }

  getGridViewContextItemsOnCellsSelection(field) {
    return [GridViewFieldAIGenerateValuesContextItem]
  }

  isEnabled() {
    const { store } = this.app
    return Object.keys(store.getters['settings/get'].generative_ai).length > 0
  }
}
