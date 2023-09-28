import { Registerable } from '@baserow/modules/core/registry'
import RowEditFieldText from '@baserow/modules/database/components/row/RowEditFieldText'
import RowEditFieldLongText from '@baserow/modules/database/components/row/RowEditFieldLongText'
import RowEditFieldNumber from '@baserow/modules/database/components/row/RowEditFieldNumber'
import RowEditFieldDateReadOnly from '@baserow/modules/database/components/row/RowEditFieldDateReadOnly'
import GridViewFieldLongText from '@baserow/modules/database/components/view/grid/fields/GridViewFieldLongText'
import RowEditFieldBoolean from '@baserow/modules/database/components/row/RowEditFieldBoolean'
import FunctionalGridViewFieldLongText from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldLongText'
import FunctionalGridViewFieldText from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldText'
import FunctionalGridViewFieldBlank from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldBlank'
import FunctionalGridViewFieldArray from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldArray'
import FunctionalGridViewFieldLink from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldLink'
import GridViewFieldArray from '@baserow/modules/database/components/view/grid/fields/GridViewFieldArray'
import RowEditFieldSingleSelectReadOnly from '@baserow/modules/database/components/row/RowEditFieldSingleSelectReadOnly'
import RowEditFieldArray from '@baserow/modules/database/components/row/RowEditFieldArray'
import RowEditFieldFormulaLink from '@baserow/modules/database/components/row/RowEditFieldFormulaLink'
import FunctionalFormulaArrayItem from '@baserow/modules/database/components/formula/array/FunctionalFormulaArrayItem'
import FunctionalFormulaBooleanArrayItem from '@baserow/modules/database/components/formula/array/FunctionalFormulaBooleanArrayItem'
import FunctionalFormulaDateArrayItem from '@baserow/modules/database/components/formula/array/FunctionalFormulaDateArrayItem'
import FunctionalFormulaSingleSelectArrayItem from '@baserow/modules/database/components/formula/array/FunctionalFormulaSingleSelectArrayItem'
import FunctionalFormulaLinkArrayItem from '@baserow/modules/database/components/formula/array/FunctionalFormulaLinkArrayItem'
import RowCardFieldArray from '@baserow/modules/database/components/card/RowCardFieldArray'
import RowEditFieldBlank from '@baserow/modules/database/components/row/RowEditFieldBlank'
import RowCardFieldBlank from '@baserow/modules/database/components/card/RowCardFieldBlank'
import RowCardFieldLink from '@baserow/modules/database/components/card/RowCardFieldLink'
import GridViewFieldLinkURL from '@baserow/modules/database/components/view/grid/fields/GridViewFieldLinkURL.vue'
import GridViewFieldText from '@baserow/modules/database/components/view/grid/fields/GridViewFieldText.vue'

export class BaserowFormulaTypeDefinition extends Registerable {
  getIconClass() {
    throw new Error(
      'Not implemented error. This method should return the types icon.'
    )
  }

  getRowEditFieldComponent() {
    throw new Error(
      'Not implemented error. This method should return the types row edit component.'
    )
  }

  getFunctionalGridViewFieldComponent() {
    return this.app.$registry
      .get('field', this.getFieldType())
      .getFunctionalGridViewFieldComponent()
  }

  getGridViewFieldComponent() {
    return this.app.$registry
      .get('field', this.getFieldType())
      .getGridViewFieldComponent()
  }

  getFieldType() {
    throw new Error(
      'Not implemented error. This method should return the types corresponding' +
        ' Baserow field type that should be used for things like sort indicators etc.'
    )
  }

  getSortOrder() {
    throw new Error(
      'Not implemented error. This method should return a number indicating how it ' +
        'should be sorted compared to other formula types when displayed.'
    )
  }

  getDocsResponseExample(field) {
    return this.app.$registry
      .get('field', this.getFieldType())
      .getDocsResponseExample(field)
  }

  getDocsDataType(field) {
    return this.app.$registry
      .get('field', this.getFieldType())
      .getDocsDataType(field)
  }

  prepareValueForCopy(field, value) {
    return this.app.$registry
      .get('field', this.getFieldType())
      .prepareValueForCopy(field, value)
  }

  getCardComponent() {
    return this.app.$registry
      .get('field', this.getFieldType())
      .getCardComponent()
  }

  getFunctionalGridViewFieldArrayComponent() {
    return FunctionalFormulaArrayItem
  }

  getCanSortInView(field) {
    return true
  }

  canBeSortedWhenInArray(field) {
    return false
  }

  getSort(name, order, field) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this.getFieldType()
    )
    return underlyingFieldType.getSort(name, order, field)
  }

  _mapFormulaTypeToFieldType(formulaType) {
    return this.app.$registry.get('formula_type', formulaType).getFieldType()
  }

  getSortIndicator(field) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this._mapFormulaTypeToFieldType(field.formula_type)
    )
    return underlyingFieldType.getSortIndicator()
  }

  mapToSortableArray(element) {
    return element.value
  }

  toHumanReadableString(field, value) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this.getFieldType()
    )
    return underlyingFieldType.toHumanReadableString(field, value)
  }

  canRepresentDate() {
    return false
  }

  canGroupByInView() {
    return false
  }
}

export class BaserowFormulaTextType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'text'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'iconoir-text'
  }

  getRowEditFieldComponent() {
    return RowEditFieldLongText
  }

  getGridViewFieldComponent() {
    return GridViewFieldLongText
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldLongText
  }

  getSortOrder() {
    return 1
  }

  canBeSortedWhenInArray(field) {
    return true
  }

  canGroupByInView() {
    return true
  }
}

export class BaserowFormulaCharType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'char'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'iconoir-text'
  }

  getRowEditFieldComponent() {
    return RowEditFieldText
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldText
  }

  getSortOrder() {
    return 1
  }

  canBeSortedWhenInArray(field) {
    return true
  }

  canGroupByInView() {
    return true
  }
}

export class BaserowFormulaNumberType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'number'
  }

  getFieldType() {
    return 'number'
  }

  getIconClass() {
    return 'baserow-icon-hashtag'
  }

  getRowEditFieldComponent() {
    return RowEditFieldNumber
  }

  getSortOrder() {
    return 2
  }

  canBeSortedWhenInArray(field) {
    return true
  }

  canGroupByInView() {
    return true
  }
}

export class BaserowFormulaBooleanType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'boolean'
  }

  getFieldType() {
    return 'boolean'
  }

  getIconClass() {
    return 'baserow-icon-circle-checked'
  }

  getRowEditFieldComponent() {
    return RowEditFieldBoolean
  }

  getSortOrder() {
    return 3
  }

  getFunctionalGridViewFieldArrayComponent() {
    return FunctionalFormulaBooleanArrayItem
  }

  canBeSortedWhenInArray(field) {
    return true
  }

  canGroupByInView() {
    return true
  }
}

export class BaserowFormulaDateType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'date'
  }

  getFieldType() {
    return 'date'
  }

  getIconClass() {
    return 'iconoir-calendar'
  }

  getRowEditFieldComponent() {
    return RowEditFieldDateReadOnly
  }

  getSortOrder() {
    return 4
  }

  getFunctionalGridViewFieldArrayComponent() {
    return FunctionalFormulaDateArrayItem
  }

  canRepresentDate() {
    return true
  }

  canBeSortedWhenInArray(field) {
    return true
  }

  mapToSortableArray(element) {
    return element.value
  }

  canGroupByInView() {
    return true
  }
}

export class BaserowFormulaDateIntervalType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'date_interval'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'baserow-icon-history'
  }

  getRowEditFieldComponent() {
    return RowEditFieldText
  }

  getGridViewFieldComponent() {
    return GridViewFieldText
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldText
  }

  getSortOrder() {
    return 5
  }

  canGroupByInView() {
    return true
  }
}

// This type only exists in the frontend and only is referenced by a few weird frontend
// function defs which we want to show as a 'special' type in the GUI.
export class BaserowFormulaSpecialType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'special'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'baserow-icon-formula'
  }

  getRowEditFieldComponent() {
    return RowEditFieldText
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldText
  }

  getSortOrder() {
    return 6
  }
}

export class BaserowFormulaInvalidType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'invalid'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'iconoir-warning-triangle'
  }

  getCardComponent() {
    return RowCardFieldBlank
  }

  getRowEditFieldComponent() {
    return RowEditFieldBlank
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldBlank
  }

  getSortOrder() {
    return 9
  }

  getCanSortInView(field) {
    return false
  }
}

export class BaserowFormulaArrayType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'array'
  }

  getFieldType(field) {
    return 'text'
  }

  getIconClass() {
    return 'iconoir-list'
  }

  getCardComponent() {
    return RowCardFieldArray
  }

  getRowEditFieldComponent() {
    return RowEditFieldArray
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldArray
  }

  getGridViewFieldComponent() {
    return GridViewFieldArray
  }

  getSortOrder() {
    return 7
  }

  prepareValueForCopy(field, value) {
    const subType = this.app.$registry.get(
      'formula_type',
      field.array_formula_type
    )
    return value
      .map((v) => {
        return subType.prepareValueForCopy(field, v.value)
      })
      .join(', ')
  }

  getDocsResponseExample(field) {
    if (field.array_formula_type != null) {
      const value = this.app.$registry
        .get('formula_type', field.array_formula_type)
        .getDocsResponseExample(field)
      return [{ id: 0, value }]
    } else {
      return null
    }
  }

  getDocsDataType(field) {
    return 'array'
  }

  getCanSortInView(field) {
    const subType = this.app.$registry.get(
      'formula_type',
      field.array_formula_type
    )
    return subType.canBeSortedWhenInArray(field)
  }

  getSort(name, order, field) {
    const subType = this.app.$registry.get(
      'formula_type',
      field.array_formula_type
    )

    const innerSortFunction = subType.getSort(name, order, field)

    return (a, b) => {
      const valuesA = a[name].map(subType.mapToSortableArray)
      const valuesB = b[name].map(subType.mapToSortableArray)

      for (let i = 0; i < Math.max(valuesA.length, valuesB.length); i++) {
        let compared = 0

        const isAdefined = valuesA[i] || valuesA[i] === ''
        const isBdefined = valuesB[i] || valuesB[i] === ''

        if (isAdefined && isBdefined) {
          compared = innerSortFunction(
            { [name]: valuesA[i] },
            { [name]: valuesB[i] }
          )
        } else if (
          isAdefined &&
          (valuesB[i] === undefined || valuesB[i] === false)
        ) {
          compared = order === 'ASC' ? 1 : -1
        } else if (
          isBdefined &&
          (valuesA[i] === undefined || valuesA[i] === false)
        ) {
          compared = order === 'ASC' ? -1 : 1
        } else if (isAdefined && valuesB[i] === null) {
          compared = order === 'ASC' ? -1 : 1
        } else if (isBdefined && valuesA[i] === null) {
          compared = order === 'ASC' ? 1 : -1
        } else if (valuesA[i] === null && valuesB[i] === undefined) {
          compared = order === 'ASC' ? 1 : -1
        } else if (valuesA[i] === undefined && valuesB[i] === null) {
          compared = order === 'ASC' ? -1 : 1
        } else if (valuesA[i] === false && valuesB[i] !== false) {
          compared = order === 'ASC' ? 1 : -1
        } else if (valuesA[i] !== false && valuesB[i] === false) {
          compared = order === 'ASC' ? -1 : 1
        }

        if (compared !== 0) {
          return compared
        }
      }
    }
  }

  getSortIndicator(field) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this._mapFormulaTypeToFieldType(field.array_formula_type)
    )
    return underlyingFieldType.getSortIndicator()
  }

  toHumanReadableString(field, value) {
    const subType = this.app.$registry.get(
      'formula_type',
      field.array_formula_type
    )
    return value
      .map((v) => {
        return subType.toHumanReadableString(field, v.value)
      })
      .join(', ')
  }

  canGroupByInView() {
    return true
  }
}

export class BaserowFormulaSingleSelectType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'single_select'
  }

  getFieldType() {
    return 'single_select'
  }

  getIconClass() {
    return 'baserow-icon-single-select'
  }

  getRowEditFieldComponent() {
    return RowEditFieldSingleSelectReadOnly
  }

  getFunctionalGridViewFieldArrayComponent() {
    return FunctionalFormulaSingleSelectArrayItem
  }

  getSortOrder() {
    return 8
  }

  getCanSortInView(field) {
    return true
  }

  canBeSortedWhenInArray(field) {
    return true
  }

  mapToSortableArray(element) {
    return element.value
  }

  canGroupByInView() {
    return true
  }
}

export class BaserowFormulaLinkType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'link'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'iconoir-link'
  }

  getRowEditFieldComponent() {
    return RowEditFieldFormulaLink
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldLink
  }

  getGridViewFieldComponent() {
    return GridViewFieldLinkURL
  }

  getSortOrder() {
    return 10
  }

  getFunctionalGridViewFieldArrayComponent() {
    return FunctionalFormulaLinkArrayItem
  }

  toHumanReadableString(field, value) {
    if (value?.label) {
      return `${value.label} (${value.url})`
    } else {
      return value.url
    }
  }

  getCardComponent() {
    return RowCardFieldLink
  }

  prepareValueForCopy(field, value) {
    return this.toHumanReadableString(field, value)
  }

  getCanSortInView(field) {
    return false
  }

  canGroupByInView() {
    return true
  }
}
