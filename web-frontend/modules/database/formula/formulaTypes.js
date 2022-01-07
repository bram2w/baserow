import { Registerable } from '@baserow/modules/core/registry'
import RowEditFieldText from '@baserow/modules/database/components/row/RowEditFieldText'
import RowEditFieldNumber from '@baserow/modules/database/components/row/RowEditFieldNumber'
import RowEditFieldDate from '@baserow/modules/database/components/row/RowEditFieldDate'
import RowEditFieldBoolean from '@baserow/modules/database/components/row/RowEditFieldBoolean'
import FunctionalGridViewFieldDate from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldDate'
import FunctionalGridViewFieldBoolean from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldBoolean'
import FunctionalGridViewFieldSingleSelect from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldSingleSelect'
import FunctionalGridViewFieldNumber from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldNumber'
import FunctionalGridViewFieldText from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldText'
import FunctionalGridViewFieldBlank from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldBlank'
import FunctionalGridViewFieldArray from '@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldArray'
import GridViewFieldArray from '@baserow/modules/database/components/view/grid/fields/GridViewFieldArray'
import RowEditFieldSingleSelectReadOnly from '@baserow/modules/database/components/row/RowEditFieldSingleSelectReadOnly'
import RowEditFieldArray from '@baserow/modules/database/components/row/RowEditFieldArray'
import FunctionalFormulaArrayItem from '@baserow/modules/database/components/formula/array/FunctionalFormulaArrayItem'
import FunctionalFormulaBooleanArrayItem from '@baserow/modules/database/components/formula/array/FunctionalFormulaBooleanArrayItem'
import FunctionalFormulaDateArrayItem from '@baserow/modules/database/components/formula/array/FunctionalFormulaDateArrayItem'
import FunctionalFormulaSingleSelectArrayItem from '@baserow/modules/database/components/formula/array/FunctionalFormulaSingleSelectArrayItem'
import RowCardFieldArray from '@baserow/modules/database/components/card/RowCardFieldArray'
import RowEditFieldBlank from '@baserow/modules/database/components/row/RowEditFieldBlank'
import RowCardFieldBlank from '@baserow/modules/database/components/card/RowCardFieldBlank'

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
    throw new Error(
      'Not implemented error. This method should return the types functional grid' +
        ' view field component.'
    )
  }

  getGridViewFieldComponent() {
    return this.getFunctionalGridViewFieldComponent()
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

  getCanSortInView() {
    return true
  }
}

export class BaserowFormulaTextType extends BaserowFormulaTypeDefinition {
  getType() {
    return 'text'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'font'
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
}

export class BaserowFormulaCharType extends BaserowFormulaTypeDefinition {
  getType() {
    return 'char'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'font'
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
}

export class BaserowFormulaNumberType extends BaserowFormulaTypeDefinition {
  getType() {
    return 'number'
  }

  getFieldType() {
    return 'number'
  }

  getIconClass() {
    return 'hashtag'
  }

  getRowEditFieldComponent() {
    return RowEditFieldNumber
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldNumber
  }

  getSortOrder() {
    return 2
  }
}

export class BaserowFormulaBooleanType extends BaserowFormulaTypeDefinition {
  getType() {
    return 'boolean'
  }

  getFieldType() {
    return 'boolean'
  }

  getIconClass() {
    return 'check-square'
  }

  getRowEditFieldComponent() {
    return RowEditFieldBoolean
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldBoolean
  }

  getSortOrder() {
    return 3
  }

  getFunctionalGridViewFieldArrayComponent() {
    return FunctionalFormulaBooleanArrayItem
  }
}

export class BaserowFormulaDateType extends BaserowFormulaTypeDefinition {
  getType() {
    return 'date'
  }

  getFieldType() {
    return 'date'
  }

  getIconClass() {
    return 'calendar-alt'
  }

  getRowEditFieldComponent() {
    return RowEditFieldDate
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldDate
  }

  getSortOrder() {
    return 4
  }

  getFunctionalGridViewFieldArrayComponent() {
    return FunctionalFormulaDateArrayItem
  }
}

export class BaserowFormulaDateIntervalType extends BaserowFormulaTypeDefinition {
  getType() {
    return 'date_interval'
  }

  getFieldType() {
    return 'date'
  }

  getIconClass() {
    return 'history'
  }

  getRowEditFieldComponent() {
    return RowEditFieldText
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldText
  }

  getSortOrder() {
    return 5
  }
}

// This type only exists in the frontend and only is referenced by a few weird frontend
// function defs which we want to show as a 'special' type in the GUI.
export class BaserowFormulaSpecialType extends BaserowFormulaTypeDefinition {
  getType() {
    return 'special'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'square-root-alt'
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
  getType() {
    return 'invalid'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'fa-exclamation-triangle'
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

  getCanSortInView() {
    return false
  }
}

export class BaserowFormulaArrayType extends BaserowFormulaTypeDefinition {
  getType() {
    return 'array'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'list'
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

  getCanSortInView() {
    return false
  }
}

export class BaserowFormulaSingleSelectType extends BaserowFormulaTypeDefinition {
  getType() {
    return 'single_select'
  }

  getFieldType() {
    return 'single_select'
  }

  getIconClass() {
    return 'chevron-circle-down '
  }

  getRowEditFieldComponent() {
    return RowEditFieldSingleSelectReadOnly
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldSingleSelect
  }

  getFunctionalGridViewFieldArrayComponent() {
    return FunctionalFormulaSingleSelectArrayItem
  }

  getSortOrder() {
    return 8
  }

  getCanSortInView() {
    return false
  }
}
