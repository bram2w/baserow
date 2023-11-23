import { firstBy } from 'thenby'
import BigNumber from 'bignumber.js'
import { maxPossibleOrderValue } from '@baserow/modules/database/viewTypes'
import { escapeRegExp } from '@baserow/modules/core/utils/string'
import { SearchModes } from '@baserow/modules/database/utils/search'
import { convertStringToMatchBackendTsvectorData } from '@baserow/modules/database/search/regexes'

/**
 * Generates a sort function based on the provided sortings.
 */
export function getRowSortFunction($registry, sortings, fields, groupBys = []) {
  let sortFunction = firstBy()
  const combined = [...groupBys, ...sortings]
  combined.forEach((sort) => {
    // Find the field that is related to the sort.
    const field = fields.find((f) => f.id === sort.field)

    if (field !== undefined) {
      const fieldName = `field_${field.id}`
      const fieldType = $registry.get('field', field.type)
      const fieldSortFunction = fieldType.getSort(fieldName, sort.order, field)
      sortFunction = sortFunction.thenBy(fieldSortFunction)
    }
  })

  sortFunction = sortFunction.thenBy((a, b) =>
    new BigNumber(a.order).minus(new BigNumber(b.order))
  )
  sortFunction = sortFunction.thenBy((a, b) => a.id - b.id)
  return sortFunction
}

/**
 * Generates a sort function for fields based on order and id.
 */
export function sortFieldsByOrderAndIdFunction(
  fieldOptions,
  primaryAlwaysFirst = false
) {
  return (a, b) => {
    if (primaryAlwaysFirst) {
      // If primary must always be first, then first by primary.
      if (a.primary > b.primary) {
        return -1
      } else if (a.primary < b.primary) {
        return 1
      }
    }

    const orderA = fieldOptions[a.id]
      ? fieldOptions[a.id].order
      : maxPossibleOrderValue
    const orderB = fieldOptions[b.id]
      ? fieldOptions[b.id].order
      : maxPossibleOrderValue

    // First by order.
    if (orderA > orderB) {
      return 1
    } else if (orderA < orderB) {
      return -1
    }

    // Then by id.
    return a.id - b.id
  }
}

/**
 * Returns only fields that are visible (not hidden).
 */
export function filterVisibleFieldsFunction(fieldOptions) {
  return (field) => {
    const exists = Object.prototype.hasOwnProperty.call(fieldOptions, field.id)
    return !exists || !fieldOptions[field.id].hidden
  }
}

/**
 * Returns only fields that are visible (not hidden).
 */
export function filterHiddenFieldsFunction(fieldOptions) {
  return (field) => {
    const exists = Object.prototype.hasOwnProperty.call(fieldOptions, field.id)
    return exists && fieldOptions[field.id].hidden
  }
}

/**
 * Represents a node in a tree structure used for grouped filters.
 * A group node is made of a filterType (AND or OR), a list of filters and a parent.
 * If the parent is null it means that it is the root node. If the parent is not
 * null it means that it is a child of the parent node, and the constructor will take care to
 * add itself to the children of the parent node, so that we can later traverse the tree
 * from the root node and check if a row matches the filters.
 */
export const TreeGroupNode = class {
  /**
   * Constructs a new TreeGroupNode.
   *
   * @param {string} filterType - The type of filter (e.g., 'AND' or 'OR').
   * @param {TreeGroupNode} [parent=null] - The parent node of this node. Null for the root node.
   */
  constructor(filterType, parent = null) {
    this.filterType = filterType
    this.parent = parent
    this.filters = []
    this.children = []
    if (parent) {
      parent.children.push(this)
    }
  }

  /**
   * Checks if this node or any of its descendants has filters.
   *
   * @returns {boolean} - True if there are filters, false otherwise.
   */
  hasFilters() {
    return this.filters.length > 0 || this.children.some((c) => c.hasFilters())
  }

  /**
   * Adds a filter object to this node list of filters.
   *
   * @param {object} filter - The filter to add.
   */
  addFilter(filter) {
    this.filters.push(filter)
  }

  /**
   * Serializes the filter tree rooted at this node. The serialized version will be in the form:
   * {
   *  filter_type: 'AND' | 'OR',
   *  filters: [
   *    {
   *       type: 'contains' | 'does_not_contain' | 'is' | 'is_not' | 'is_empty' | 'is_not_empty' | etc.,
   *       field: 1,
   *       value: 'some value'
   *     },
   *     ...
   *   ],
   *   groups: [
   *     {
   *        filter_type: 'AND' | 'OR',
   *        filters: [
   *          type: 'contains' | 'does_not_contain' | 'is' | 'is_not' | 'is_empty' | 'is_not_empty' | etc.,
   *          field: 2,
   *          value: 'some other value'
   *        },
   *        ...
   *        ],
   *       groups: [...]
   *     },
   *    ...,
   *   ],
   * }
   *
   * @returns {object} - The serialized tree.
   */
  getFiltersTreeSerialized() {
    const serialized = {
      filter_type: this.filterType,
      filters: [],
      groups: [],
    }

    for (const filter of this.filters) {
      serialized.filters.push({
        type: filter.type,
        field: filter.field,
        value: filter.value,
      })
    }

    for (const groupNode of this.children) {
      serialized.groups.push(groupNode.getFiltersTreeSerialized())
    }
    return serialized
  }

  /**
   * Determines if a given row matches the conditions of this node and its descendants.
   * This function will recursively check if the row matches the filters of this node
   * and its descendants. If the filter type of this node is 'AND' then it will return
   * true if the row matches all the filters. If the filter type of this node is 'OR'
   * then it will return true if the row matches at least one of the filters.
   *
   * @param {object} $registry - The registry containing field and filter type information.
   * @param {Array} fields - The list of fields.
   * @param {object} rowValues - The values of the row being checked.
   * @returns {boolean} - True if the row matches, false otherwise.
   */
  matches($registry, fields, rowValues) {
    for (const child of this.children) {
      const matches = child.matches($registry, fields, rowValues)
      if (this.filterType === 'AND' && !matches) {
        return false
      } else if (this.filterType === 'OR' && matches) {
        return true
      }
    }
    for (const filter of this.filters) {
      const filterValue = filter.value
      const field = fields.find((f) => f.id === filter.field)
      const fieldType = $registry.get('field', field.type)
      const viewFilterType = $registry.get('viewFilter', filter.type)
      const rowValue = rowValues[`field_${field.id}`]
      const matches = viewFilterType.matches(
        rowValue,
        filterValue,
        field,
        fieldType
      )
      if (this.filterType === 'AND' && !matches) {
        // With an `AND` filter type, the row must match all the filters, so if
        // one of the filters doesn't match we can mark it as invalid.
        return false
      } else if (this.filterType === 'OR' && matches) {
        // With an 'OR' filter type, the row only has to match one of the filters,
        // that is the case here so we can mark it as valid.
        return true
      }
    }
    if (this.filterType === 'AND') {
      // At this point with an `AND` condition the filter type matched all the
      // filters and therefore we can mark it as valid.
      return true
    } else if (this.filterType === 'OR') {
      // At this point with an `OR` condition none of the filters matched and
      // therefore we can mark it as invalid.
      return false
    }
  }
}

/**
 * Creates a tree structure from given filters and filter groups. Groups are
 * first sorted by ID because parent groups have smaller IDs since they were
 * created before their children. In this way, we ensure that when a child node
 * is added to the tree, its parent will already be present.
 * Once the tree has been created, it adds all the filters to the respective
 * groups.
 *
 * @param {string} filterType - The root filter type.
 * @param {Array} filters - The list of filters.
 * @param {Array} filterGroups - The list of filter groups.
 * @returns {TreeGroupNode} - The root of the filter tree.
 */
export const createFiltersTree = (filterType, filters, filterGroups) => {
  const rootGroup = new TreeGroupNode(filterType)
  const filterGroupsById = { '': rootGroup }
  const filterGroupsOrderedById = filterGroups
    ? [...filterGroups].sort((a, b) => a.id - b.id)
    : []

  for (const filterGroup of filterGroupsOrderedById) {
    const parent = filterGroupsById[filterGroup.parent || '']
    filterGroupsById[filterGroup.id] = new TreeGroupNode(
      filterGroup.filter_type,
      parent
    )
  }

  for (const filter of filters) {
    const filterGroupId = filter.group || ''
    const filterGroup = filterGroupsById[filterGroupId]
    filterGroup.addFilter(filter)
  }
  return rootGroup
}

/**
 * A helper function that checks if the provided row values match the provided view
 * filters. Returning false indicates that the row should not be visible for that
 * view.
 */
export const matchSearchFilters = (
  $registry,
  filterType,
  filters,
  filterGroups,
  fields,
  values
) => {
  // If there aren't any filters then it is not possible to check if the row
  // matches any of the filters, so we can mark it as valid.
  if (filters.length === 0) {
    return true
  }

  const filterTree = createFiltersTree(filterType, filters, filterGroups)
  return filterTree.matches($registry, fields, values)
}

function _fullTextSearch(registry, field, value, activeSearchTerm) {
  const searchableString = registry
    .get('field', field.type)
    .toSearchableString(field, value)
  const fixedValue = convertStringToMatchBackendTsvectorData(searchableString)
  const fixedTerm = convertStringToMatchBackendTsvectorData(activeSearchTerm)
  if (fixedTerm.length === 0) {
    return false
  } else {
    const regexMatchingWordsThatStartWithTerm =
      '(^|\\s+)' + escapeRegExp(fixedTerm)
    return !!fixedValue.match(
      new RegExp(regexMatchingWordsThatStartWithTerm, 'gu')
    )
  }
}

function _compatSearchMode(registry, field, value, activeSearchTerm) {
  return registry
    .get('field', field.type)
    .containsFilter(value, activeSearchTerm, field)
}

export function valueMatchesActiveSearchTerm(
  searchMode,
  registry,
  field,
  value,
  activeSearchTerm
) {
  if (searchMode === SearchModes.MODE_FT_WITH_COUNT) {
    return _fullTextSearch(registry, field, value, activeSearchTerm)
  } else {
    return _compatSearchMode(registry, field, value, activeSearchTerm)
  }
}

function _findFieldsInRowMatchingSearch(
  row,
  activeSearchTerm,
  fields,
  registry,
  overrides,
  searchMode
) {
  const fieldSearchMatches = new Set()
  // If the row is loading then a temporary UUID is put in its id. We don't want to
  // accidentally match against that UUID as it will be shortly replaced with its
  // real id.
  if (
    !row._.loading &&
    row.id?.toString() === (activeSearchTerm || '').trim()
  ) {
    fieldSearchMatches.add('row_id')
  }
  for (const field of fields) {
    const fieldName = `field_${field.id}`
    const rowValue =
      fieldName in overrides ? overrides[fieldName] : row[fieldName]
    if (rowValue !== undefined && rowValue !== null) {
      const doesMatch = valueMatchesActiveSearchTerm(
        searchMode,
        registry,
        field,
        rowValue,
        activeSearchTerm
      )
      if (doesMatch) {
        fieldSearchMatches.add(field.id.toString())
      }
    }
  }

  return fieldSearchMatches
}

/**
 * Helper function which calculates if a given row and which of it's fields matches a
 * given search term. The rows values can be overridden by providing an overrides
 * object containing a mapping of the field name to override to a value that will be
 * used to check for matches instead of the rows real one. The rows values will not be
 * changed.
 */
export function calculateSingleRowSearchMatches(
  row,
  activeSearchTerm,
  hideRowsNotMatchingSearch,
  fields,
  registry,
  searchMode,
  overrides = {}
) {
  const searchIsBlank = activeSearchTerm === ''
  const fieldSearchMatches = searchIsBlank
    ? new Set()
    : _findFieldsInRowMatchingSearch(
        row,
        activeSearchTerm,
        fields,
        registry,
        overrides,
        searchMode
      )

  const matchSearch =
    !hideRowsNotMatchingSearch || searchIsBlank || fieldSearchMatches.size > 0
  return { row, matchSearch, fieldSearchMatches }
}

/**
 * Returns true is the empty value of the provided field matches the active search term.
 */
export function newFieldMatchesActiveSearchTerm(
  registry,
  newField,
  activeSearchTerm
) {
  if (newField && activeSearchTerm !== '') {
    const fieldType = registry.get('field', newField.type)
    const emptyValue = fieldType.getEmptyValue(newField)

    return valueMatchesActiveSearchTerm(
      registry,
      newField,
      emptyValue,
      activeSearchTerm
    )
  }
  return false
}

export function getGroupBy(rootGetters, viewId) {
  if (rootGetters['page/view/public/getIsPublic']) {
    const view = rootGetters['view/get'](viewId)
    return view.group_bys
      .map((groupBy) => {
        return `${groupBy.order === 'DESC' ? '-' : ''}field_${groupBy.field}`
      })
      .join(',')
  } else {
    return ''
  }
}

export function getOrderBy(rootGetters, viewId) {
  if (rootGetters['page/view/public/getIsPublic']) {
    const view = rootGetters['view/get'](viewId)
    return view.sortings
      .map((sort) => {
        return `${sort.order === 'DESC' ? '-' : ''}field_${sort.field}`
      })
      .join(',')
  } else {
    return ''
  }
}

export function getFilters(rootGetters, viewId) {
  const payload = {}

  if (rootGetters['page/view/public/getIsPublic']) {
    const view = rootGetters['view/get'](viewId)

    if (!view.filters_disabled) {
      const {
        filter_type: filterType,
        filter_groups: filterGroups,
        filters,
      } = view
      const filterTree = createFiltersTree(filterType, filters, filterGroups)
      if (filterTree.hasFilters()) {
        const serializedTree = filterTree.getFiltersTreeSerialized()
        payload.filters = [JSON.stringify(serializedTree)]
      }
    }
    return payload
  }
}

/**
 * Calculates the size of a UTF-8 encoded string in bytes - computes the size
 * of a string in UTF-8 encoding and utilizes the TextEncoder API if available.
 *
 * Using TextEncoder is preferred in Modern Browsers and Node.js Supported
 * environments because it provides a more efficient and accurate way to encode
 * strings into UTF-8 bytes and directly calculate the byte size of the encoded
 * string.
 *
 * In some older web browsers or environments where TextEncoder may not be available
 * (such as SSR where certain browser APIs are absent), it falls back to a less
 * accurate method and simply returns the length of the string.
 */
export function utf8ByteSize(str) {
  // Use TextEncoder if available (modern browsers and Node.js)
  if (typeof TextEncoder !== 'undefined') {
    const encoder = new TextEncoder()
    const data = encoder.encode(str)
    return data.length
  } else {
    // Fallback for older browsers (may not be as accurate)
    return str.length
  }
}

/**
 * Limit the size of a cookie's value by removing elements from an array
 * until it fits within the maximum allowed cookie size.
 */
export function fitInCookie(name, list) {
  const result = []
  for (let i = list.length - 1; i >= 0; i--) {
    result.unshift(list[i])
    const serialized = encodeURIComponent(JSON.stringify(result))
    if (utf8ByteSize(serialized) > 4096) {
      result.shift() // Remove the last added item as it caused the size to exceed the limit
      break
    }
  }
  return result
}

/**
 * Return the view that has been visited most recently or the first
 * available one that is capable of displaying the provided row data if required.
 * If no view is available that can display the row data, return undefined.
 */
export function getDefaultView(app, store, workspaceId, showRowModal) {
  // Put the most recently visited one first in the list.
  const defaultView = store.getters['view/default']
  const allViews = store.getters['view/getAllOrdered']
  const views = defaultView ? [defaultView, ...allViews] : allViews

  return views.find((view) => {
    const viewType = app.$registry.get('view', view.type)
    if (viewType.isDeactivated(workspaceId)) {
      return false
    }
    // Ensure that the view can display the row data if required.
    return showRowModal ? viewType.canShowRowModal() : true
  })
}
