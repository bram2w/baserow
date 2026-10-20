import { lazyComponent } from '@baserow/modules/core/utils/lazyComponent'
import RowCardFieldArray from '@baserow/modules/database/components/card/RowCardFieldArray'
import RowCardFieldBlank from '@baserow/modules/database/components/card/RowCardFieldBlank'
import RowCardFieldLinkURL from '@baserow/modules/database/components/card/RowCardFieldLinkURL'
import RowCardFieldButton from '@baserow/modules/database/components/card/RowCardFieldButton'
import RowCardFieldSingleFile from '@baserow/modules/database/components/card/RowCardFieldSingleFile'
import RowCardFieldURL from '@baserow/modules/database/components/card/RowCardFieldURL'
import { Registerable } from '@baserow/modules/core/registry'
import { mix } from '@baserow/modules/core/mixins'
import {
  hasEmptyValueFilterMixin,
  hasValueEqualFilterMixin,
  hasValueContainsFilterMixin,
  hasValueContainsWordFilterMixin,
  hasValueLengthIsLowerThanFilterMixin,
  hasSelectOptionIdEqualMixin,
  hasSelectOptionValueContainsFilterMixin,
  hasSelectOptionValueContainsWordFilterMixin,
  baserowFormulaArrayTypeFilterMixin,
  hasNumericValueComparableToFilterMixin,
  hasNestedSelectOptionValueContainsFilterMixin,
  hasNestedSelectOptionValueContainsWordFilterMixin,
  hasMultipleSelectOptionIdEqualMixin,
} from '@baserow/modules/database/arrayFilterMixins'
import _ from 'lodash'
import {
  genericHasAllValuesEqualFilter,
  genericHasValueContainsFilter,
  genericHasValueContainsWordFilter,
} from '@baserow/modules/database/utils/fieldFilters'
import { DEFAULT_SORT_TYPE_KEY } from '@baserow/modules/database/constants'

const RowEditFieldText = lazyComponent(
  () => import('@baserow/modules/database/components/row/RowEditFieldText')
)
const RowEditFieldLongText = lazyComponent(
  () => import('@baserow/modules/database/components/row/RowEditFieldLongText')
)
const RowEditFieldNumber = lazyComponent(
  () => import('@baserow/modules/database/components/row/RowEditFieldNumber')
)
const RowEditFieldDateReadOnly = lazyComponent(
  () =>
    import('@baserow/modules/database/components/row/RowEditFieldDateReadOnly')
)
const GridViewFieldLongText = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/GridViewFieldLongText')
)
const RowEditFieldBoolean = lazyComponent(
  () => import('@baserow/modules/database/components/row/RowEditFieldBoolean')
)
const FunctionalGridViewFieldLongText = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldLongText')
)
const FunctionalGridViewFieldText = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldText')
)
const FunctionalGridViewFieldBlank = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldBlank')
)
const FunctionalGridViewFieldArray = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldArray')
)
const FunctionalGridViewFieldButton = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldButton')
)
const FunctionalGridViewFieldLinkURL = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldLinkURL')
)
const GridViewFieldArray = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/GridViewFieldArray')
)
const RowEditFieldSingleSelectReadOnly = lazyComponent(
  () =>
    import('@baserow/modules/database/components/row/RowEditFieldSingleSelectReadOnly')
)
const RowEditFieldMultipleSelectReadOnly = lazyComponent(
  () =>
    import('@baserow/modules/database/components/row/RowEditFieldMultipleSelectReadOnly')
)
const RowEditFieldMultipleCollaboratorsReadOnly = lazyComponent(
  () =>
    import('@baserow/modules/database/components/row/RowEditFieldMultipleCollaboratorsReadOnly')
)
const RowEditFieldArray = lazyComponent(
  () => import('@baserow/modules/database/components/row/RowEditFieldArray')
)
const RowEditFieldLinkURL = lazyComponent(
  () => import('@baserow/modules/database/components/row/RowEditFieldLinkURL')
)
const RowEditFieldButton = lazyComponent(
  () => import('@baserow/modules/database/components/row/RowEditFieldButton')
)
const RowEditFieldDurationReadOnly = lazyComponent(
  () =>
    import('@baserow/modules/database/components/row/RowEditFieldDurationReadOnly')
)
const FunctionalFormulaArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaArrayItem')
)
const FunctionalFormulaArrayDurationItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaArrayDurationItem')
)
const FunctionalFormulaArrayNumberItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaArrayNumberItem')
)
const FunctionalFormulaBooleanArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaBooleanArrayItem')
)
const FunctionalFormulaDateArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaDateArrayItem')
)
const FunctionalFormulaSingleSelectArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaSingleSelectArrayItem')
)
const FunctionalFormulaMultipleSelectArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaMultipleSelectArrayItem')
)
const FunctionalFormulaMultipleCollaboratorsArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaMultipleCollaboratorsArrayItem')
)
const FunctionalFormulaLinkArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaLinkArrayItem')
)
const FunctionalFormulaButtonArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaButtonArrayItem')
)
const RowEditFieldBlank = lazyComponent(
  () => import('@baserow/modules/database/components/row/RowEditFieldBlank')
)
const GridViewFieldButton = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/GridViewFieldButton')
)
const GridViewFieldLinkURL = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/GridViewFieldLinkURL')
)
const GridViewFieldText = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/GridViewFieldText')
)
const RowEditFieldFileReadOnly = lazyComponent(
  () =>
    import('@baserow/modules/database/components/row/RowEditFieldFileReadOnly')
)
const FunctionalGridViewSingleFile = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/FunctionalGridViewSingleFile')
)
const FunctionalFormulaFileArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaFileArrayItem')
)
const SingleFileArrayModal = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/SingleFileArrayModal')
)
const GridViewSingleFile = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/GridViewSingleFile')
)
const RowEditSingleFileReadOnly = lazyComponent(
  () =>
    import('@baserow/modules/database/components/row/RowEditSingleFileReadOnly')
)
const RowEditFieldURL = lazyComponent(
  () => import('@baserow/modules/database/components/row/RowEditFieldURL')
)
const FunctionalGridViewFieldURL = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/FunctionalGridViewFieldURL')
)
const GridViewFieldURL = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/grid/fields/GridViewFieldURL')
)
const FunctionalFormulaURLArrayItem = lazyComponent(
  () =>
    import('@baserow/modules/database/components/formula/array/FunctionalFormulaURLArrayItem')
)
const ViewFilterTypeBoolean = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/ViewFilterTypeBoolean')
)
const ViewFilterTypeDuration = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/ViewFilterTypeDuration')
)
const ViewFilterTypeMultipleSelectOptions = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/ViewFilterTypeMultipleSelectOptions')
)
const ViewFilterTypeCollaborators = lazyComponent(
  () =>
    import('@baserow/modules/database/components/view/ViewFilterTypeCollaborators')
)

export class BaserowFormulaTypeDefinition extends Registerable {
  getIconClass() {
    throw new Error(
      'Not implemented error. This method should return the types icon.'
    )
  }

  getRowEditFieldComponent(field) {
    throw new Error(
      'Not implemented error. This method should return the types row edit component.'
    )
  }

  getFilterInputComponent(field, filterType) {
    return this.app.$registry
      .get('field', this.getFieldType())
      .getFilterInputComponent(field, filterType)
  }

  getRowEditArrayFieldComponent() {
    return null
  }

  parseFilterValue(field, value) {
    return this.app.$registry
      .get('field', this.getFieldType())
      .parseFilterValue(field, value)
  }

  formatFilterValue(field, value) {
    return this.app.$registry
      .get('field', this.getFieldType())
      .formatFilterValue(field, value)
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

  parseInputValue(field, value) {
    return this.app.$registry
      .get('field', this.getFieldType())
      .parseInputValue(field, value)
  }

  getCardComponent() {
    return this.app.$registry
      .get('field', this.getFieldType())
      .getCardComponent()
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaArrayItem
  }

  getCanSortInView(field) {
    return true
  }

  canBeSortedWhenInArray(field) {
    return false
  }

  getItemIsInNestedValueObjectWhenInArray() {
    return true
  }

  /**
   * The extra modal is a component that can be opened by emitting the `show` event up.
   */
  getExtraModal() {
    return null
  }

  getSort(name, order, field) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this.getFieldType()
    )
    return underlyingFieldType.getSort(name, order, field)
  }

  getSortTypes(field) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this.getFieldType()
    )
    const fieldSortTypes = underlyingFieldType.getSortTypes(field)
    // Only the default sort type is supported for formulas at the moment because
    // there is no way to configure different types in the backend.
    return {
      [DEFAULT_SORT_TYPE_KEY]: fieldSortTypes[DEFAULT_SORT_TYPE_KEY],
    }
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
    return this.getItemIsInNestedValueObjectWhenInArray()
      ? element.value
      : element
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

  isEqual(field, value1, value2) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this._mapFormulaTypeToFieldType(field.formula_type)
    )
    return underlyingFieldType.isEqual(field, value1, value2)
  }

  getRowValueFromGroupValue(field, value) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this._mapFormulaTypeToFieldType(field.formula_type)
    )
    return underlyingFieldType.getRowValueFromGroupValue(field, value)
  }

  getGroupValueFromRowValue(field, value) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this._mapFormulaTypeToFieldType(field.formula_type)
    )
    return underlyingFieldType.getGroupValueFromRowValue(field, value)
  }

  canRepresentFiles(field) {
    return false
  }

  toBaserowFormulaType(field) {
    return this.getType()
  }

  parseFromLinkedRowItemValue(field, value) {
    const underlyingFieldType = this.app.$registry.get(
      'field',
      this._mapFormulaTypeToFieldType(field.formula_type)
    )
    return underlyingFieldType.parseFromLinkedRowItemValue(field, value)
  }
}

export class BaserowFormulaTextType extends mix(
  hasEmptyValueFilterMixin,
  hasValueEqualFilterMixin,
  hasValueContainsFilterMixin,
  hasValueContainsWordFilterMixin,
  hasValueLengthIsLowerThanFilterMixin,
  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'text'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'iconoir-text'
  }

  getRowEditFieldComponent(field) {
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

export class BaserowFormulaCharType extends mix(
  hasEmptyValueFilterMixin,
  hasValueEqualFilterMixin,
  hasValueContainsFilterMixin,
  hasValueContainsWordFilterMixin,
  hasValueLengthIsLowerThanFilterMixin,
  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'char'
  }

  getFieldType() {
    return 'text'
  }

  getIconClass() {
    return 'iconoir-text'
  }

  getRowEditFieldComponent(field) {
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

export class BaserowFormulaNumberType extends mix(
  hasEmptyValueFilterMixin,
  hasValueContainsFilterMixin,
  hasNumericValueComparableToFilterMixin,

  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'number'
  }

  getFieldType() {
    return 'number'
  }

  getIconClass() {
    return 'baserow-icon-hashtag'
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldNumber
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaArrayNumberItem
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

  getRowEditFieldComponent(field) {
    return RowEditFieldBoolean
  }

  getSortOrder() {
    return 3
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaBooleanArrayItem
  }

  canBeSortedWhenInArray(field) {
    return true
  }

  canGroupByInView() {
    return true
  }

  getFilterInputComponent(field, filterType) {
    return ViewFilterTypeBoolean
  }

  getHasAllValuesEqualFilterFunction(field) {
    return (cellValue, filterValue) => {
      const parsedValue = this.parseInputValue(field, filterValue)
      return genericHasAllValuesEqualFilter(cellValue, parsedValue)
    }
  }

  getHasValueContainsFilterFunction(field) {
    return (cellValue, filterValue) => {
      const parsedValue = this.parseInputValue(field, filterValue)
      return genericHasValueContainsFilter(cellValue, parsedValue)
    }
  }

  getHasValueEqualFilterFunction(field) {
    return this.app.$registry
      .get('field', this.getFieldType())
      .getHasValueEqualFilterFunction(field)
  }

  parseInputValue(field, filterValue) {
    if (filterValue === '') {
      return false
    }
    return super.parseInputValue(field, filterValue)
  }
}

export class BaserowFormulaDateType extends mix(
  hasEmptyValueFilterMixin,
  hasValueContainsFilterMixin,
  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'date'
  }

  getFieldType() {
    return 'date'
  }

  getIconClass() {
    return 'iconoir-calendar'
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldDateReadOnly
  }

  getSortOrder() {
    return 4
  }

  getFunctionalFieldArrayComponent() {
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

export class BaserowFormulaDurationType extends mix(
  hasEmptyValueFilterMixin,
  hasNumericValueComparableToFilterMixin,
  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'duration'
  }

  getFieldType() {
    return 'duration'
  }

  getIconClass() {
    return 'iconoir-clock-rotate-right'
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldDurationReadOnly
  }

  getFilterInputComponent(field, filterType) {
    return ViewFilterTypeDuration
  }

  getSortOrder() {
    return 5
  }

  canGroupByInView() {
    return true
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaArrayDurationItem
  }

  canBeSortedWhenInArray(field) {
    return true
  }
}

// Deprecated, use BaserowFormulaDurationType instead.
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

  getRowEditFieldComponent(field) {
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

  getRowEditFieldComponent(field) {
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

  getRowEditFieldComponent(field) {
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

export class BaserowFormulaArrayType extends mix(
  baserowFormulaArrayTypeFilterMixin,
  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'array'
  }

  getFieldType(field) {
    return 'text'
  }

  parseInputValue(field, value) {
    return this.getSubType(field)?.parseInputValue(field, value)
  }

  getIconClass() {
    return 'iconoir-list'
  }

  getCardComponent() {
    return RowCardFieldArray
  }

  parseFilterValue(field, value) {
    const subType = this.getSubType(field)
    if (subType == null) {
      return value
    }
    return subType.parseFilterValue(field, value)
  }

  formatFilterValue(field, value) {
    const subType = this.getSubType(field)
    if (subType == null) {
      return value
    }
    return subType.formatFilterValue(field, value)
  }

  getSubType(field) {
    return this.app.$registry.get('formula_type', field.array_formula_type)
  }

  getRowEditFieldComponent(field) {
    const arrayOverride =
      this.getSubType(field)?.getRowEditArrayFieldComponent()
    if (arrayOverride) {
      return arrayOverride
    } else {
      return RowEditFieldArray
    }
  }

  getFilterInputComponent(field, filterType) {
    return this.getSubType(field)?.getFilterInputComponent(field, filterType)
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
    const subType = this.getSubType(field)
    return value
      .map((v) => {
        return subType.prepareValueForCopy(
          field,
          subType.getItemIsInNestedValueObjectWhenInArray() ? v.value : v
        )
      })
      .join(', ')
  }

  getDocsResponseExample(field) {
    if (field.array_formula_type != null) {
      const subType = this.getSubType(field)
      const value = this.app.$registry
        .get('formula_type', field.array_formula_type)
        .getDocsResponseExample(field)
      if (subType.getItemIsInNestedValueObjectWhenInArray()) {
        return [{ id: 0, value }]
      } else {
        return [value]
      }
    } else {
      return null
    }
  }

  getDocsDataType(field) {
    return 'array'
  }

  getCanSortInView(field) {
    const subType = this.getSubType(field)
    return subType.canBeSortedWhenInArray(field)
  }

  canRepresentFiles(field) {
    const subType = this.getSubType(field)
    return subType.canRepresentFiles(field)
  }

  getSort(name, order, field) {
    const subType = this.getSubType(field)

    const innerSortFunction = subType.getSort(name, order, field)
    const toArray = (value) =>
      Array.isArray(value) ? value : value == null ? [] : [value]
    const mapToSortable = subType.mapToSortableArray.bind(subType)
    const isDefined = (value) => value || value === '' || value === 0

    return (a, b) => {
      const valuesA = toArray(a[name]).map(mapToSortable)
      const valuesB = toArray(b[name]).map(mapToSortable)

      for (let i = 0; i < Math.max(valuesA.length, valuesB.length); i++) {
        let compared = 0

        const isAdefined = isDefined(valuesA[i])
        const isBdefined = isDefined(valuesB[i])

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

  getSortTypes(field) {
    return {
      [DEFAULT_SORT_TYPE_KEY]: {
        function: this.getSort.bind(this),
        indicator: this.getSortIndicator(field),
      },
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
    const subType = this.getSubType(field)
    if (!Array.isArray(value)) {
      return ''
    }

    return value
      .map((v) => {
        return subType.toHumanReadableString(
          field,
          subType.getItemIsInNestedValueObjectWhenInArray() ? v.value : v
        )
      })
      .join(', ')
  }

  canGroupByInView() {
    return false
  }

  toBaserowFormulaType(field) {
    return this.getSubType(field)?.toBaserowFormulaType(field)
  }

  parseFromLinkedRowItemValue(field, value) {
    const subType = this.getSubType(field)
    return subType.parseFromLinkedRowItemValue(field, value)
  }
}

export class BaserowFormulaFileType extends BaserowFormulaTypeDefinition {
  static getType() {
    return 'single_file'
  }

  getFieldType() {
    return 'file'
  }

  getIconClass() {
    return 'iconoir-empty-page'
  }

  getRowEditArrayFieldComponent() {
    return RowEditFieldFileReadOnly
  }

  getRowEditFieldComponent(field) {
    return RowEditSingleFileReadOnly
  }

  getItemIsInNestedValueObjectWhenInArray() {
    return false
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewSingleFile
  }

  getGridViewFieldComponent() {
    return GridViewSingleFile
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaFileArrayItem
  }

  getExtraModal() {
    return SingleFileArrayModal
  }

  getSortOrder() {
    return 11
  }

  getCanSortInView(field) {
    return false
  }

  canBeSortedWhenInArray(field) {
    return false
  }

  canGroupByInView() {
    return false
  }

  getDocsResponseExample(field) {
    return {
      url: 'https://files.baserow.io/user_files/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
      thumbnails: {
        tiny: {
          url: 'https://files.baserow.io/media/thumbnails/tiny/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
          width: 21,
          height: 21,
        },
        small: {
          url: 'https://files.baserow.io/media/thumbnails/small/VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
          width: 48,
          height: 48,
        },
      },
      name: 'VXotniBOVm8tbstZkKsMKbj2Qg7KmPvn_39d354a76abe56baaf569ad87d0333f58ee4bf3eed368e3b9dc736fd18b09dfd.png',
      size: 229940,
      mime_type: 'image/png',
      is_image: true,
      image_width: 1280,
      image_height: 585,
      uploaded_at: '2020-11-17T12:16:10.035234+00:00',
    }
  }

  getDocsDataType(field) {
    return 'single_file'
  }

  prepareValueForCopy(field, value) {
    return `${value?.visible_name} (${value?.url})`
  }

  getCardComponent() {
    return RowCardFieldSingleFile
  }

  toHumanReadableString(field, value) {
    return value?.visible_name || ''
  }

  canRepresentFiles(field) {
    return true
  }
}

export class BaserowFormulaSingleSelectType extends mix(
  hasEmptyValueFilterMixin,
  hasSelectOptionIdEqualMixin,
  hasSelectOptionValueContainsFilterMixin,
  hasSelectOptionValueContainsWordFilterMixin,
  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'single_select'
  }

  getFieldType() {
    return 'single_select'
  }

  getIconClass() {
    return 'baserow-icon-single-select'
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldSingleSelectReadOnly
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaSingleSelectArrayItem
  }

  getFilterInputComponent(field, filterType) {
    return ViewFilterTypeMultipleSelectOptions
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
    return false
  }
}

export class BaserowFormulaMultipleSelectType extends mix(
  hasEmptyValueFilterMixin,
  hasNestedSelectOptionValueContainsFilterMixin,
  hasNestedSelectOptionValueContainsWordFilterMixin,
  hasMultipleSelectOptionIdEqualMixin,
  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'multiple_select'
  }

  getFieldType() {
    return 'multiple_select'
  }

  getIconClass() {
    return 'baserow-icon-multiple-select'
  }

  getFilterInputComponent(field, filterType) {
    return ViewFilterTypeMultipleSelectOptions
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldMultipleSelectReadOnly
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaMultipleSelectArrayItem
  }

  getSortOrder() {
    return 8
  }

  getCanSortInView(field) {
    return false
  }

  canBeSortedWhenInArray(field) {
    return false
  }

  mapToSortableArray(element) {
    return element.value
  }

  canGroupByInView() {
    return false
  }
}

export class BaserowFormulaMultipleCollaboratorsType extends mix(
  hasEmptyValueFilterMixin,
  hasNestedSelectOptionValueContainsFilterMixin,
  hasNestedSelectOptionValueContainsWordFilterMixin,
  hasMultipleSelectOptionIdEqualMixin,
  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'multiple_collaborators'
  }

  getFieldType() {
    return 'multiple_collaborators'
  }

  getIconClass() {
    return 'iconoir-community'
  }

  getFilterInputComponent(field, filterType) {
    return ViewFilterTypeCollaborators
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldMultipleCollaboratorsReadOnly
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaMultipleCollaboratorsArrayItem
  }

  getSortOrder() {
    return 8
  }

  getCanSortInView(field) {
    return false
  }

  canBeSortedWhenInArray(field) {
    return false
  }

  mapToSortableArray(element) {
    return element.value
  }

  canGroupByInView() {
    return false
  }

  _getHasValueEqualFilterFunctionForRowValues(rowValueIdSets, filterValues) {
    return rowValueIdSets.some((rowValueIdSet) =>
      rowValueIdSet.isSupersetOf(new Set(filterValues))
    )
  }

  _getHasValueContainsFilterFunction(cellValue, filterValue) {
    return cellValue.some((v) =>
      genericHasValueContainsFilter(v?.value || [], filterValue, 'name')
    )
  }

  _getHasValueContainsWordFilterFunction(cellValue, filterValue) {
    return cellValue.some((v) =>
      genericHasValueContainsWordFilter(v?.value || [], filterValue, 'name')
    )
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

  getRowEditFieldComponent(field) {
    return RowEditFieldLinkURL
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldLinkURL
  }

  getGridViewFieldComponent() {
    return GridViewFieldLinkURL
  }

  getSortOrder() {
    return 10
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaLinkArrayItem
  }

  toHumanReadableString(field, value) {
    if (value == null) {
      return ''
    }
    if (value.label) {
      return `${value.label} (${value.url})`
    } else {
      return value.url
    }
  }

  getCardComponent() {
    return RowCardFieldLinkURL
  }

  prepareValueForCopy(field, value) {
    return this.toHumanReadableString(field, value)
  }

  getCanSortInView(field) {
    return false
  }

  canGroupByInView() {
    return false
  }
}

export class BaserowFormulaURLType extends mix(
  hasEmptyValueFilterMixin,
  hasValueEqualFilterMixin,
  hasValueContainsFilterMixin,
  hasValueContainsWordFilterMixin,
  hasValueLengthIsLowerThanFilterMixin,
  BaserowFormulaTypeDefinition
) {
  static getType() {
    return 'url'
  }

  getFieldType() {
    return 'url'
  }

  getIconClass() {
    return 'iconoir-link'
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldURL
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldURL
  }

  getGridViewFieldComponent() {
    return GridViewFieldURL
  }

  getSortOrder() {
    return 10
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaURLArrayItem
  }

  toHumanReadableString(field, value) {
    if (value == null) {
      return ''
    }
    if (_.isString(value)) {
      return value
    }
    if (value.label) {
      return `${value.label} (${value.url})`
    } else {
      return value.url
    }
  }

  getCardComponent() {
    return RowCardFieldURL
  }

  prepareValueForCopy(field, value) {
    return this.toHumanReadableString(field, value)
  }

  getCanSortInView(field) {
    return false
  }

  canGroupByInView() {
    return false
  }
}

export class BaserowFormulaButtonType extends BaserowFormulaLinkType {
  static getType() {
    return 'button'
  }

  getRowEditFieldComponent(field) {
    return RowEditFieldButton
  }

  getFunctionalGridViewFieldComponent() {
    return FunctionalGridViewFieldButton
  }

  getGridViewFieldComponent() {
    return GridViewFieldButton
  }

  getCardComponent() {
    return RowCardFieldButton
  }

  getFunctionalFieldArrayComponent() {
    return FunctionalFormulaButtonArrayItem
  }
}
