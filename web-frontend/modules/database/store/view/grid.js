import Vue from 'vue'
import axios from 'axios'
import _ from 'lodash'
import BigNumber from 'bignumber.js'

import { uuid } from '@baserow/modules/core/utils/string'
import { clone } from '@baserow/modules/core/utils/object'
import ViewService from '@baserow/modules/database/services/view'
import GridService from '@baserow/modules/database/services/view/grid'
import RowService from '@baserow/modules/database/services/row'
import {
  calculateSingleRowSearchMatches,
  getRowSortFunction,
  matchSearchFilters,
  getFilters,
  getOrderBy,
} from '@baserow/modules/database/utils/view'
import { RefreshCancelledError } from '@baserow/modules/core/errors'
import { prepareRowForRequest } from '@baserow/modules/database/utils/row'

export function populateRow(row, metadata = {}) {
  row._ = {
    metadata,
    loading: false,
    hover: false,
    selectedBy: [],
    matchFilters: true,
    matchSortings: true,
    // Whether the row should be displayed based on the current activeSearchTerm term.
    matchSearch: true,
    // Contains the specific field ids which match the activeSearchTerm term.
    // Could be empty even when matchSearch is true when there is no
    // activeSearchTerm term applied.
    fieldSearchMatches: [],
    // Keeping the selected state with the row has the best performance when navigating
    // between cells.
    selected: false,
    selectedFieldId: -1,
  }
  return row
}

function extractMetadataAndPopulateRow(data, rowIndex) {
  const metadata = data.row_metadata || {}
  const row = data.results[rowIndex]
  populateRow(row, metadata[row.id])
}

export const state = () => ({
  // Indicates if multiple cell selection is active
  multiSelectActive: false,
  // Indicates if the user is clicking and holding the mouse over a cell
  multiSelectHolding: false,
  /**
   * The indexes for head and tail cells in a multi-select grid.
   * Multi-Select works by tracking four different indexes, these are:
   *   - The field and row index for the first cell selected, known as the head.
   *   - The field and row index for the last cell selected, known as the tail.
   * All the cells between the head and tail cells are later also calculated as selected.
   */
  multiSelectHeadRowIndex: -1,
  multiSelectHeadFieldIndex: -1,
  multiSelectTailRowIndex: -1,
  multiSelectTailFieldIndex: -1,
  // The last used grid id.
  lastGridId: -1,
  // Contains the custom field options per view. Things like the field width are
  // stored here.
  fieldOptions: {},
  // Contains the buffered rows that we keep in memory. Depending on the
  // scrollOffset rows will be added or removed from this buffer. Most of the times,
  // it will contain 3 times the bufferRequestSize in rows.
  rows: [],
  // The total amount of rows in the table.
  count: 0,
  // The height of a single row.
  rowHeight: 33,
  // The distance to the top in pixels the visible rows should have.
  rowsTop: 0,
  // The amount of rows that must be visible above and under the middle row.
  rowPadding: 16,
  // The amount of rows that will be requested per request.
  bufferRequestSize: 40,
  // The start index of the buffer in the whole table.
  bufferStartIndex: 0,
  // The limit of the buffer measured from the start index in the whole table.
  bufferLimit: 0,
  // The start index of the visible rows of the rows in the buffer.
  rowsStartIndex: 0,
  // The end index of the visible rows of the rows buffer.
  rowsEndIndex: 0,
  // The last scrollTop when the visibleByScrollTop was called.
  scrollTop: 0,
  // The height of the window where the rows are displayed in.
  windowHeight: 0,
  // Indicates if the user is hovering over the add row button.
  addRowHover: false,
  // A user provided optional search term which can be used to filter down rows.
  activeSearchTerm: '',
  // If true then the activeSearchTerm will be sent to the server to filter rows
  // entirely out. When false no server filter will be applied and rows which do not
  // have any matching cells will still be displayed.
  hideRowsNotMatchingSearch: true,
  fieldAggregationData: {},
})

export const mutations = {
  CLEAR_ROWS(state) {
    state.fieldOptions = {}
    state.count = 0
    state.rows = []
    state.rowsTop = 0
    state.bufferStartIndex = 0
    state.bufferLimit = 0
    state.rowsStartIndex = 0
    state.rowsEndIndex = 0
    state.scrollTop = 0
    state.addRowHover = false
    state.activeSearchTerm = ''
    state.hideRowsNotMatchingSearch = true
  },
  SET_SEARCH(state, { activeSearchTerm, hideRowsNotMatchingSearch }) {
    state.activeSearchTerm = activeSearchTerm
    state.hideRowsNotMatchingSearch = hideRowsNotMatchingSearch
  },
  SET_LAST_GRID_ID(state, gridId) {
    state.lastGridId = gridId
  },
  SET_SCROLL_TOP(state, scrollTop) {
    state.scrollTop = scrollTop
  },
  SET_WINDOW_HEIGHT(state, value) {
    state.windowHeight = value
  },
  SET_ROW_PADDING(state, value) {
    state.rowPadding = value
  },
  SET_BUFFER_START_INDEX(state, value) {
    state.bufferStartIndex = value
  },
  SET_BUFFER_LIMIT(state, value) {
    state.bufferLimit = value
  },
  SET_COUNT(state, value) {
    state.count = value
  },
  SET_ROWS_INDEX(state, { startIndex, endIndex, top }) {
    state.rowsStartIndex = startIndex
    state.rowsEndIndex = endIndex
    state.rowsTop = top
  },
  SET_ADD_ROW_HOVER(state, value) {
    state.addRowHover = value
  },
  /**
   * It will add and remove rows to the state based on the provided values. For example
   * if prependToRows is a positive number that amount of the provided rows will be
   * added to the state. If that number is negative that amount will be removed from
   * the state. Same goes for the appendToRows, only then it will be appended.
   */
  ADD_ROWS(
    state,
    { rows, prependToRows, appendToRows, count, bufferStartIndex, bufferLimit }
  ) {
    state.count = count
    state.bufferStartIndex = bufferStartIndex
    state.bufferLimit = bufferLimit

    if (prependToRows > 0) {
      state.rows = [...rows.slice(0, prependToRows), ...state.rows]
    }
    if (appendToRows > 0) {
      state.rows.push(...rows.slice(0, appendToRows))
    }

    if (prependToRows < 0) {
      state.rows = state.rows.splice(Math.abs(prependToRows))
    }
    if (appendToRows < 0) {
      state.rows = state.rows.splice(
        0,
        state.rows.length - Math.abs(appendToRows)
      )
    }
  },
  REPLACE_ALL_FIELD_OPTIONS(state, fieldOptions) {
    state.fieldOptions = fieldOptions
  },
  UPDATE_ALL_FIELD_OPTIONS(state, fieldOptions) {
    state.fieldOptions = _.merge({}, state.fieldOptions, fieldOptions)
  },
  /**
   * Only adds the new field options and removes the deleted ones. The existing ones
   * will be left untouched.
   */
  ADD_MISSING_FIELD_OPTIONS(state, fieldOptions) {
    // Add the missing field options.
    Object.keys(fieldOptions).forEach((key) => {
      const exists = Object.prototype.hasOwnProperty.call(
        state.fieldOptions,
        key
      )
      if (!exists) {
        Vue.set(state.fieldOptions, key, fieldOptions[key])
      }
    })

    // Remove the deleted ones.
    Object.keys(state.fieldOptions).forEach((key) => {
      const exists = Object.prototype.hasOwnProperty.call(fieldOptions, key)
      if (!exists) {
        Vue.delete(state.fieldOptions, key)
      }
    })
  },
  UPDATE_FIELD_OPTIONS_OF_FIELD(state, { fieldId, values }) {
    if (Object.prototype.hasOwnProperty.call(state.fieldOptions, fieldId)) {
      Object.assign(state.fieldOptions[fieldId], values)
    } else {
      state.fieldOptions = Object.assign({}, state.fieldOptions, {
        [fieldId]: values,
      })
    }
  },
  DELETE_FIELD_OPTIONS(state, fieldId) {
    if (Object.prototype.hasOwnProperty.call(state.fieldOptions, fieldId)) {
      delete state.fieldOptions[fieldId]
    }
  },
  SET_ROW_HOVER(state, { row, value }) {
    row._.hover = value
  },
  SET_ROW_LOADING(state, { row, value }) {
    row._.loading = value
  },
  SET_ROW_SEARCH_MATCHES(state, { row, matchSearch, fieldSearchMatches }) {
    row._.fieldSearchMatches.slice(0).forEach((value) => {
      if (!fieldSearchMatches.has(value)) {
        const index = row._.fieldSearchMatches.indexOf(value)
        row._.fieldSearchMatches.splice(index, 1)
      }
    })
    fieldSearchMatches.forEach((value) => {
      if (!row._.fieldSearchMatches.includes(value)) {
        row._.fieldSearchMatches.push(value)
      }
    })
    row._.matchSearch = matchSearch
  },
  SET_ROW_MATCH_FILTERS(state, { row, value }) {
    row._.matchFilters = value
  },
  SET_ROW_MATCH_SORTINGS(state, { row, value }) {
    row._.matchSortings = value
  },
  ADD_ROW_SELECTED_BY(state, { row, fieldId }) {
    if (!row._.selectedBy.includes(fieldId)) {
      row._.selectedBy.push(fieldId)
    }
  },
  REMOVE_ROW_SELECTED_BY(state, { row, fieldId }) {
    const index = row._.selectedBy.indexOf(fieldId)
    if (index > -1) {
      row._.selectedBy.splice(index, 1)
    }
  },
  SET_SELECTED_CELL(state, { rowId, fieldId }) {
    state.rows.forEach((row) => {
      if (row._.selected) {
        row._.selected = false
        row._.selectedFieldId = -1
      }
      if (row.id === rowId) {
        row._.selected = true
        row._.selectedFieldId = fieldId
      }
    })
  },
  UPDATE_MULTISELECT(state, { position, rowIndex, fieldIndex }) {
    if (position === 'head') {
      state.multiSelectHeadRowIndex = rowIndex
      state.multiSelectHeadFieldIndex = fieldIndex
    } else if (position === 'tail') {
      // Limit selection to 200 rows (199 since rows start at index 0)
      // This limit is set by the backend
      if (Math.abs(state.multiSelectHeadRowIndex - rowIndex) <= 199) {
        state.multiSelectTailRowIndex = rowIndex
        state.multiSelectTailFieldIndex = fieldIndex
      }
    }
  },
  SET_MULTISELECT_HOLDING(state, value) {
    state.multiSelectHolding = value
  },
  SET_MULTISELECT_ACTIVE(state, value) {
    state.multiSelectActive = value
  },
  CLEAR_MULTISELECT(state) {
    state.multiSelectHolding = false
    state.multiSelectHeadRowIndex = -1
    state.multiSelectHeadFieldIndex = -1
    state.multiSelectTailRowIndex = -1
    state.multiSelectTailFieldIndex = -1
  },
  ADD_FIELD_TO_ROWS_IN_BUFFER(state, { field, value }) {
    const name = `field_${field.id}`
    // We have to replace all the rows by using the map function to make it
    // reactive and update immediately. If we don't do this, the value in the
    // field components of the grid and modal don't always have the correct value
    // binding.
    state.rows = state.rows.map((row) => {
      if (!Object.prototype.hasOwnProperty.call(row, name)) {
        row[`field_${field.id}`] = value
      }
      return { ...row }
    })
  },
  DECREASE_ORDERS_IN_BUFFER_LOWER_THAN(state, existingOrder) {
    const min = new BigNumber(existingOrder).integerValue(BigNumber.ROUND_FLOOR)
    const max = new BigNumber(existingOrder)

    // Decrease all the orders that have already have been inserted before the same
    // row.
    state.rows.forEach((row) => {
      const order = new BigNumber(row.order)
      if (order.isGreaterThan(min) && order.isLessThanOrEqualTo(max)) {
        row.order = order
          .minus(new BigNumber('0.00000000000000000001'))
          .toString()
      }
    })
  },
  INSERT_NEW_ROW_IN_BUFFER_AT_INDEX(state, { row, index }) {
    state.count++
    state.bufferLimit++

    // If another row with the same order already exists, then we need to decrease all
    // the other orders that are within the range by '0.00000000000000000001'.
    if (
      state.rows.findIndex((r) => r.id !== row.id && r.order === row.order) > -1
    ) {
      const min = new BigNumber(row.order).integerValue(BigNumber.ROUND_FLOOR)
      const max = new BigNumber(row.order)

      // Decrease all the orders that have already have been inserted before the same
      // row.
      state.rows.forEach((row) => {
        const order = new BigNumber(row.order)
        if (order.isGreaterThan(min) && order.isLessThanOrEqualTo(max)) {
          row.order = order
            .minus(new BigNumber('0.00000000000000000001'))
            .toString()
        }
      })
    }

    state.rows.splice(index, 0, row)
  },
  INSERT_EXISTING_ROW_IN_BUFFER_AT_INDEX(state, { row, index }) {
    state.rows.splice(index, 0, row)
  },
  MOVE_EXISTING_ROW_IN_BUFFER(state, { row, index }) {
    const oldIndex = state.rows.findIndex((item) => item.id === row.id)
    if (oldIndex !== -1) {
      state.rows.splice(index, 0, state.rows.splice(oldIndex, 1)[0])
    }
  },
  UPDATE_ROW_IN_BUFFER(state, { row, values, metadata = false }) {
    const index = state.rows.findIndex((item) => item.id === row.id)
    if (index !== -1) {
      const existingRowState = state.rows[index]
      Object.assign(existingRowState, values)
      if (metadata) {
        existingRowState._.metadata = metadata
      }
    }
  },
  UPDATE_ROW_FIELD_VALUE(state, { row, field, value }) {
    row[`field_${field.id}`] = value
  },
  UPDATE_ROW_METADATA(state, { row, rowMetadataType, updateFunction }) {
    const currentValue = row._.metadata[rowMetadataType]
    Vue.set(row._.metadata, rowMetadataType, updateFunction(currentValue))
  },
  FINALIZE_ROW_IN_BUFFER(state, { oldId, id, order, values }) {
    const index = state.rows.findIndex((item) => item.id === oldId)
    if (index !== -1) {
      state.rows[index].id = id
      state.rows[index].order = order
      state.rows[index]._.loading = false
      Object.keys(values).forEach((key) => {
        state.rows[index][key] = values[key]
      })
    }
  },
  /**
   * Deletes a row of which we are sure that it is in the buffer right now.
   */
  DELETE_ROW_IN_BUFFER(state, row) {
    const index = state.rows.findIndex((item) => item.id === row.id)
    if (index !== -1) {
      state.count--
      state.bufferLimit--
      state.rows.splice(index, 1)
    }
  },
  /**
   * Deletes a row from the buffer without updating the buffer limit and count.
   */
  DELETE_ROW_IN_BUFFER_WITHOUT_UPDATE(state, row) {
    const index = state.rows.findIndex((item) => item.id === row.id)
    if (index !== -1) {
      state.rows.splice(index, 1)
    }
  },
  SET_FIELD_AGGREGATION_DATA(state, { fieldId, value: newValue }) {
    const current = state.fieldAggregationData[fieldId] || {
      loading: false,
    }

    state.fieldAggregationData = {
      ...state.fieldAggregationData,
      [fieldId]: { ...current, value: newValue },
    }
  },
  SET_FIELD_AGGREGATION_DATA_LOADING(
    state,
    { fieldId, value: newLoadingValue }
  ) {
    const current = state.fieldAggregationData[fieldId] || {
      value: null,
    }

    state.fieldAggregationData = {
      ...state.fieldAggregationData,
      [fieldId]: { ...current, loading: newLoadingValue },
    }
  },
}

// Contains the info needed for the delayed scroll top action.
const fireScrollTop = {
  last: Date.now(),
  timeout: null,
  processing: false,
  distance: 0,
}

// Contains the last row request to be able to cancel it.
let lastRequest = null
let lastRequestOffset = null
let lastRequestLimit = null
let lastRefreshRequest = null
let lastRefreshRequestController = null
let lastQueryController = null

// We want to cancel previous aggregation request before creating a new one.
const lastAggregationRequest = { request: null, controller: null }

export const actions = {
  /**
   * This action calculates which rows we would like to have in the buffer based on
   * the scroll top offset and the window height. Based on that is calculates which
   * rows we need to fetch compared to what we already have. If we need to fetch
   * anything other then we already have or waiting for a new request will be made.
   */
  fetchByScrollTop(
    { commit, getters, rootGetters, dispatch },
    { scrollTop, fields }
  ) {
    const windowHeight = getters.getWindowHeight
    const gridId = getters.getLastGridId

    // Calculate what the middle row index of the visible window based on the scroll
    // top.
    const middle = scrollTop + windowHeight / 2
    const countIndex = getters.getCount - 1
    const middleRowIndex = Math.min(
      Math.max(Math.ceil(middle / getters.getRowHeight) - 1, 0),
      countIndex
    )

    // Calculate the start and end index of the rows that are visible to the user in
    // the whole database.
    const visibleStartIndex = Math.max(
      middleRowIndex - getters.getRowPadding,
      0
    )
    const visibleEndIndex = Math.min(
      middleRowIndex + getters.getRowPadding,
      countIndex
    )

    // Calculate the start and end index of the buffer, which are the rows that we
    // load in the memory of the browser, based on all the rows in the database.
    const bufferRequestSize = getters.getBufferRequestSize
    const bufferStartIndex = Math.max(
      Math.ceil((visibleStartIndex - bufferRequestSize) / bufferRequestSize) *
        bufferRequestSize,
      0
    )
    const bufferEndIndex = Math.min(
      Math.ceil((visibleEndIndex + bufferRequestSize) / bufferRequestSize) *
        bufferRequestSize,
      getters.getCount
    )
    const bufferLimit = bufferEndIndex - bufferStartIndex

    // Determine if the user is scrolling up or down.
    const down =
      bufferStartIndex > getters.getBufferStartIndex ||
      bufferEndIndex > getters.getBufferEndIndex
    const up =
      bufferStartIndex < getters.getBufferStartIndex ||
      bufferEndIndex < getters.getBufferEndIndex

    let prependToBuffer = 0
    let appendToBuffer = 0
    let requestOffset = null
    let requestLimit = null

    // Calculate how many rows we want to add and remove from the current rows buffer in
    // the store if the buffer would transition to the desired state. Also the
    // request offset and limit are calculated for the next request based on what we
    // currently have in the buffer.
    if (down) {
      prependToBuffer = Math.max(
        -getters.getBufferLimit,
        getters.getBufferStartIndex - bufferStartIndex
      )
      appendToBuffer = Math.min(
        bufferLimit,
        bufferEndIndex - getters.getBufferEndIndex
      )
      requestOffset = Math.max(getters.getBufferEndIndex, bufferStartIndex)
      requestLimit = appendToBuffer
    } else if (up) {
      prependToBuffer = Math.min(
        bufferLimit,
        getters.getBufferStartIndex - bufferStartIndex
      )
      appendToBuffer = Math.max(
        -getters.getBufferLimit,
        bufferEndIndex - getters.getBufferEndIndex
      )
      requestOffset = Math.max(bufferStartIndex, 0)
      requestLimit = prependToBuffer
    }

    // Checks if we need to request anything and if there are any changes since the
    // last request we made. If so we need to initialize a new request.
    if (
      requestLimit > 0 &&
      (lastRequestOffset !== requestOffset || lastRequestLimit !== requestLimit)
    ) {
      fireScrollTop.processing = true
      // If another request is running we need to cancel that one because it won't
      // what we need at the moment.
      if (lastRequest !== null) {
        lastQueryController.abort()
      }

      // Doing the actual request and remember what we are requesting so we can compare
      // it when making a new request.
      lastRequestOffset = requestOffset
      lastRequestLimit = requestLimit
      lastQueryController = new AbortController()
      lastRequest = GridService(this.$client)
        .fetchRows({
          gridId,
          offset: requestOffset,
          limit: requestLimit,
          signal: lastQueryController.signal,
          search: getters.getServerSearchTerm,
          publicUrl: rootGetters['page/view/public/getIsPublic'],
          publicAuthToken: rootGetters['page/view/public/getAuthToken'],
          orderBy: getOrderBy(rootGetters, getters.getLastGridId),
          filters: getFilters(rootGetters, getters.getLastGridId),
        })
        .then(({ data }) => {
          data.results.forEach((part, index) => {
            extractMetadataAndPopulateRow(data, index)
          })
          commit('ADD_ROWS', {
            rows: data.results,
            prependToRows: prependToBuffer,
            appendToRows: appendToBuffer,
            count: data.count,
            bufferStartIndex,
            bufferLimit,
          })
          dispatch('visibleByScrollTop')
          dispatch('updateSearch', { fields })
          lastRequest = null
          fireScrollTop.processing = false
        })
        .catch((error) => {
          if (!axios.isCancel(error)) {
            lastRequest = null
            throw error
          }
          fireScrollTop.processing = false
        })
    }
  },
  /**
   * Calculates which rows should be visible for the user based on the provided
   * scroll top and window height. Because we know what the padding above and below
   * the middle row should be and which rows we have in the buffer we can calculate
   * what the start and end index for the visible rows in the buffer should be.
   */
  visibleByScrollTop({ getters, commit }, scrollTop = null) {
    if (scrollTop !== null) {
      commit('SET_SCROLL_TOP', scrollTop)
    } else {
      scrollTop = getters.getScrollTop
    }

    const windowHeight = getters.getWindowHeight
    const middle = scrollTop + windowHeight / 2
    const countIndex = getters.getCount - 1

    const middleRowIndex = Math.min(
      Math.max(Math.ceil(middle / getters.getRowHeight) - 1, 0),
      countIndex
    )

    // Calculate the start and end index of the rows that are visible to the user in
    // the whole table.
    const visibleStartIndex = Math.max(
      middleRowIndex - getters.getRowPadding,
      0
    )
    const visibleEndIndex = Math.min(
      middleRowIndex + getters.getRowPadding + 1,
      getters.getCount
    )

    // Calculate the start and end index of the buffered rows that are visible for
    // the user.
    const visibleRowStartIndex =
      Math.min(
        Math.max(visibleStartIndex, getters.getBufferStartIndex),
        getters.getBufferEndIndex
      ) - getters.getBufferStartIndex
    const visibleRowEndIndex =
      Math.max(
        Math.min(visibleEndIndex, getters.getBufferEndIndex),
        getters.getBufferStartIndex
      ) - getters.getBufferStartIndex

    // Calculate the top position of the html element that contains all the rows.
    // This element will be placed over the placeholder the correct position of
    // those rows.
    const top =
      Math.min(visibleStartIndex, getters.getBufferEndIndex) *
      getters.getRowHeight

    // If the index changes from what we already have we can commit the new indexes
    // to the state.
    if (
      visibleRowStartIndex !== getters.getRowsStartIndex ||
      visibleRowEndIndex !== getters.getRowsEndIndex ||
      top !== getters.getRowsTop
    ) {
      commit('SET_ROWS_INDEX', {
        startIndex: visibleRowStartIndex,
        endIndex: visibleRowEndIndex,
        top,
      })
    }
  },
  /**
   * This action is called every time the users scrolls which might result in a lot
   * of calls. Therefore it will dispatch the related actions, but only every 100
   * milliseconds to prevent calling the actions who do a lot of calculating a lot.
   */
  fetchByScrollTopDelayed({ dispatch }, { scrollTop, fields }) {
    const now = Date.now()

    const fire = (scrollTop) => {
      fireScrollTop.distance = scrollTop
      fireScrollTop.last = now
      dispatch('fetchByScrollTop', {
        scrollTop,
        fields,
      })
      dispatch('visibleByScrollTop', scrollTop)
    }

    const distance = Math.abs(scrollTop - fireScrollTop.distance)
    const timeDelta = now - fireScrollTop.last
    const velocity = distance / timeDelta

    if (!fireScrollTop.processing && timeDelta > 100 && velocity < 2.5) {
      clearTimeout(fireScrollTop.timeout)
      fire(scrollTop)
    } else {
      // Allow velocity calculation on last ~100 ms
      if (timeDelta > 100) {
        fireScrollTop.distance = scrollTop
        fireScrollTop.last = now
      }
      clearTimeout(fireScrollTop.timeout)
      fireScrollTop.timeout = setTimeout(() => {
        fire(scrollTop)
      }, 100)
    }
  },
  /**
   * Fetches an initial set of rows and adds that data to the store.
   */
  async fetchInitial(
    { dispatch, commit, getters, rootGetters },
    { gridId, fields }
  ) {
    // Reset scrollTop when switching table
    fireScrollTop.distance = 0
    fireScrollTop.last = Date.now()
    fireScrollTop.processing = false

    commit('SET_SEARCH', {
      activeSearchTerm: '',
      hideRowsNotMatchingSearch: true,
    })
    commit('SET_LAST_GRID_ID', gridId)

    const limit = getters.getBufferRequestSize * 2
    const { data } = await GridService(this.$client).fetchRows({
      gridId,
      offset: 0,
      limit,
      includeFieldOptions: true,
      search: getters.getServerSearchTerm,
      publicUrl: rootGetters['page/view/public/getIsPublic'],
      publicAuthToken: rootGetters['page/view/public/getAuthToken'],
      orderBy: getOrderBy(rootGetters, getters.getLastGridId),
      filters: getFilters(rootGetters, getters.getLastGridId),
    })
    data.results.forEach((part, index) => {
      extractMetadataAndPopulateRow(data, index)
    })
    commit('CLEAR_ROWS')
    commit('ADD_ROWS', {
      rows: data.results,
      prependToRows: 0,
      appendToRows: data.results.length,
      count: data.count,
      bufferStartIndex: 0,
      bufferLimit: data.count > limit ? limit : data.count,
    })
    commit('SET_ROWS_INDEX', {
      startIndex: 0,
      // @TODO mut calculate how many rows would fit and based on that calculate
      // what the end index should be.
      endIndex: data.count > 31 ? 31 : data.count,
      top: 0,
    })
    commit('REPLACE_ALL_FIELD_OPTIONS', data.field_options)
    dispatch('updateSearch', { fields })
  },
  /**
   * Refreshes the current state with fresh data. It keeps the scroll offset the same
   * if possible. This can be used when a new filter or sort is created. Will also
   * update search highlighting if a new activeSearchTerm and hideRowsNotMatchingSearch
   * are provided in the refreshEvent.
   */
  refresh(
    { dispatch, commit, getters, rootGetters },
    { view, fields, includeFieldOptions = false }
  ) {
    const gridId = getters.getLastGridId

    if (lastRefreshRequest !== null) {
      lastRefreshRequestController.abort()
    }
    lastRefreshRequestController = new AbortController()
    lastRefreshRequest = GridService(this.$client)
      .fetchCount({
        gridId,
        search: getters.getServerSearchTerm,
        signal: lastRefreshRequestController.signal,
        publicUrl: rootGetters['page/view/public/getIsPublic'],
        publicAuthToken: rootGetters['page/view/public/getAuthToken'],
        filters: getFilters(rootGetters, getters.getLastGridId),
      })
      .then((response) => {
        const count = response.data.count

        const limit = getters.getBufferRequestSize * 3
        const bufferEndIndex = getters.getBufferEndIndex
        const offset =
          count >= bufferEndIndex
            ? getters.getBufferStartIndex
            : Math.max(0, count - limit)
        return { limit, offset }
      })
      .then(({ limit, offset }) =>
        GridService(this.$client)
          .fetchRows({
            gridId,
            offset,
            limit,
            includeFieldOptions,
            signal: lastRefreshRequestController.signal,
            search: getters.getServerSearchTerm,
            publicUrl: rootGetters['page/view/public/getIsPublic'],
            publicAuthToken: rootGetters['page/view/public/getAuthToken'],
            orderBy: getOrderBy(rootGetters, getters.getLastGridId),
            filters: getFilters(rootGetters, getters.getLastGridId),
          })
          .then(({ data }) => ({
            data,
            offset,
          }))
      )
      .then(({ data, offset }) => {
        // If there are results we can replace the existing rows so that the user stays
        // at the same scroll offset.
        data.results.forEach((part, index) => {
          extractMetadataAndPopulateRow(data, index)
        })
        commit('ADD_ROWS', {
          rows: data.results,
          prependToRows: -getters.getBufferLimit,
          appendToRows: data.results.length,
          count: data.count,
          bufferStartIndex: offset,
          bufferLimit: data.results.length,
        })
        dispatch('updateSearch', { fields })
        if (includeFieldOptions) {
          if (rootGetters['page/view/public/getIsPublic']) {
            // If the view is public, then we're in read only mode and we want to
            // keep our existing field options state. So in that case, we only need
            // to add the missing ones.
            commit('ADD_MISSING_FIELD_OPTIONS', data.field_options)
          } else {
            commit('REPLACE_ALL_FIELD_OPTIONS', data.field_options)
          }
        }
        dispatch('fetchAllFieldAggregationData', {
          view,
        })
        lastRefreshRequest = null
      })
      .catch((error) => {
        if (axios.isCancel(error)) {
          throw new RefreshCancelledError()
        } else {
          lastRefreshRequest = null
          throw error
        }
      })
    return lastRefreshRequest
  },
  /**
   * Updates the field options of a given field and also makes an API request to the
   * backend with the changed values. If the request fails the action is reverted.
   */
  async updateFieldOptionsOfField(
    { commit, getters, dispatch, rootGetters },
    { field, values, oldValues, readOnly = false }
  ) {
    const previousOptions = getters.getAllFieldOptions[field.id]
    let needAggregationValueUpdate = false

    /**
     * If the aggregation raw type has changed, we delete the corresponding the
     * aggregation value from the store.
     */
    if (
      Object.prototype.hasOwnProperty.call(values, 'aggregation_raw_type') &&
      values.aggregation_raw_type !== previousOptions.aggregation_raw_type
    ) {
      needAggregationValueUpdate = true
      commit('SET_FIELD_AGGREGATION_DATA', { fieldId: field.id, value: null })
      commit('SET_FIELD_AGGREGATION_DATA_LOADING', {
        fieldId: field.id,
        value: true,
      })
    }

    commit('UPDATE_FIELD_OPTIONS_OF_FIELD', {
      fieldId: field.id,
      values,
    })

    const gridId = getters.getLastGridId
    if (!readOnly) {
      const updateValues = { field_options: {} }
      updateValues.field_options[field.id] = values

      try {
        await ViewService(this.$client).updateFieldOptions({
          viewId: gridId,
          values: updateValues,
        })
      } catch (error) {
        commit('UPDATE_FIELD_OPTIONS_OF_FIELD', {
          fieldId: field.id,
          values: oldValues,
        })
        throw error
      } finally {
        if (needAggregationValueUpdate && values.aggregation_type) {
          dispatch('fetchAllFieldAggregationData', { view: { id: gridId } })
        }
      }
    }
  },
  /**
   * Updates the field options of a given field in the store. So no API request to
   * the backend is made.
   */
  setFieldOptionsOfField({ commit, getters }, { field, values }) {
    commit('UPDATE_FIELD_OPTIONS_OF_FIELD', {
      fieldId: field.id,
      values,
    })
  },
  /**
   * Replaces all field options with new values and also makes an API request to the
   * backend with the changed values. If the request fails the action is reverted.
   */
  async updateAllFieldOptions(
    { dispatch, getters, rootGetters },
    {
      newFieldOptions,
      oldFieldOptions,
      readOnly = false,
      undoRedoActionGroupId = null,
    }
  ) {
    dispatch('forceUpdateAllFieldOptions', newFieldOptions)

    const gridId = getters.getLastGridId
    if (!readOnly) {
      const updateValues = { field_options: newFieldOptions }

      try {
        await ViewService(this.$client).updateFieldOptions({
          viewId: gridId,
          values: updateValues,
          undoRedoActionGroupId,
        })
      } catch (error) {
        dispatch('forceUpdateAllFieldOptions', oldFieldOptions)
        throw error
      }
    }
  },
  /**
   * Forcefully updates all field options without making a call to the backend.
   */
  forceUpdateAllFieldOptions({ commit }, fieldOptions) {
    commit('UPDATE_ALL_FIELD_OPTIONS', fieldOptions)
  },
  /**
   * Fetch all field aggregation data from the server for this view. Set loading state
   * to true while doing the query. Do nothing if this is a public view or if there is
   * no aggregation at all. If the query goes in error, the values are set to `null`
   * to prevent wrong information.
   * If a request is already in progress, it is aborted in favour of the new one.
   */
  async fetchAllFieldAggregationData(
    { rootGetters, getters, commit },
    { view }
  ) {
    const isPublic = rootGetters['page/view/public/getIsPublic']
    const search = getters.getActiveSearchTerm

    if (isPublic) {
      return
    }

    const fieldOptions = getters.getAllFieldOptions

    let atLeastOneAggregation = false

    Object.entries(fieldOptions).forEach(([fieldId, options]) => {
      if (options.aggregation_raw_type) {
        commit('SET_FIELD_AGGREGATION_DATA_LOADING', {
          fieldId,
          value: true,
        })
        atLeastOneAggregation = true
      }
    })

    if (!atLeastOneAggregation) {
      return
    }

    try {
      if (lastAggregationRequest.request !== null) {
        lastAggregationRequest.controller.abort()
      }

      lastAggregationRequest.controller = new AbortController()
      lastAggregationRequest.request = GridService(
        this.$client
      ).fetchFieldAggregations({
        gridId: view.id,
        search,
        signal: lastAggregationRequest.controller.signal,
      })

      const { data } = await lastAggregationRequest.request
      lastAggregationRequest.request = null

      Object.entries(fieldOptions).forEach(([fieldId, options]) => {
        if (options.aggregation_raw_type) {
          commit('SET_FIELD_AGGREGATION_DATA', {
            fieldId,
            value: data[`field_${fieldId}`],
          })
        }
      })

      Object.entries(fieldOptions).forEach(([fieldId, options]) => {
        if (options.aggregation_raw_type) {
          commit('SET_FIELD_AGGREGATION_DATA_LOADING', {
            fieldId,
            value: false,
          })
        }
      })
    } catch (error) {
      if (!axios.isCancel(error)) {
        lastAggregationRequest.request = null

        // Emptied the values
        Object.entries(fieldOptions).forEach(([fieldId, options]) => {
          if (options.aggregation_raw_type) {
            commit('SET_FIELD_AGGREGATION_DATA', {
              fieldId,
              value: null,
            })
          }
        })

        // Remove loading state
        Object.entries(fieldOptions).forEach(([fieldId, options]) => {
          if (options.aggregation_raw_type) {
            commit('SET_FIELD_AGGREGATION_DATA_LOADING', {
              fieldId,
              value: false,
            })
          }
        })

        throw error
      }
    }
  },
  /**
   * Updates the order of all the available field options. The provided order parameter
   * should be an array containing the field ids in the correct order.
   */
  async updateFieldOptionsOrder(
    { commit, getters, dispatch },
    { order, readOnly = false, undoRedoActionGroupId = null }
  ) {
    const oldFieldOptions = clone(getters.getAllFieldOptions)
    const newFieldOptions = clone(getters.getAllFieldOptions)

    // Update the order of the field options that have not been provided in the order.
    // They will get a position that places them after the provided field ids.
    let i = 0
    Object.keys(newFieldOptions).forEach((fieldId) => {
      if (!order.includes(parseInt(fieldId))) {
        newFieldOptions[fieldId].order = order.length + i
        i++
      }
    })

    // Update create the field options and set the correct order value.
    order.forEach((fieldId, index) => {
      const id = fieldId.toString()
      if (Object.prototype.hasOwnProperty.call(newFieldOptions, id)) {
        newFieldOptions[fieldId.toString()].order = index
      }
    })

    return await dispatch('updateAllFieldOptions', {
      oldFieldOptions,
      newFieldOptions,
      readOnly,
      undoRedoActionGroupId,
    })
  },
  /**
   * Move one field on the left or the right of the specified `fromField`
   * by updating all the fieldOptions orders.
   *
   * @param {object} fieldToMove The field that is going to be moved.
   * @param {string} position Set to 'left' to move the field to the left of the
   *                          fromField. The field is moved to the right otherwise.
   * @param {object} fromField We want to move the `fieldtoMove` relatively to this
   *                           field.
   *                           If `position` === 'left' the `fieldToMove` is going to be
   *                           positioned at the left of the specified `fromField`
   *                           otherwise to the right of this field.
   * @param {string} undoRedoActionGroupId An optional undo/redo group action.
   * @param {boolean} readOnly Set to true to not send the modification to the server.
   */
  async updateSingleFieldOptionOrder(
    { getters, dispatch },
    {
      fieldToMove,
      position = 'left',
      fromField,
      undoRedoActionGroupId = null,
      readOnly = false,
    }
  ) {
    const oldFieldOptions = clone(getters.getAllFieldOptions)
    const newFieldOptions = clone(getters.getAllFieldOptions)

    // Order field options by order then by fieldId
    const orderedFieldOptions = Object.entries(newFieldOptions)
      .map(([fieldIdStr, options]) => [parseInt(fieldIdStr), options])
      .sort(([a, { order: orderA }], [b, { order: orderB }]) => {
        // First by order.
        if (orderA > orderB) {
          return 1
        } else if (orderA < orderB) {
          return -1
        }

        return a - b
      })

    let index = 0
    // Update order of all fieldOptions inserting the movedField to the right position
    orderedFieldOptions.forEach(([fieldId, options]) => {
      if (fieldId === fromField.id) {
        // Update firstField and second field order
        if (position === 'left') {
          newFieldOptions[fieldToMove.id].order = index
          newFieldOptions[fromField.id].order = index + 1
        } else {
          newFieldOptions[fromField.id].order = index
          newFieldOptions[fieldToMove.id].order = index + 1
        }
        index += 2
      } else if (fieldId !== fieldToMove.id) {
        // Update all other field order
        options.order = index
        index += 1
      }
    })

    return await dispatch('updateAllFieldOptions', {
      oldFieldOptions,
      newFieldOptions,
      readOnly,
      undoRedoActionGroupId,
    })
  },
  /**
   * Deletes the field options of the provided field id if they exist.
   */
  forceDeleteFieldOptions({ commit }, fieldId) {
    commit('DELETE_FIELD_OPTIONS', fieldId)
  },
  setWindowHeight({ dispatch, commit, getters }, value) {
    commit('SET_WINDOW_HEIGHT', value)
    commit('SET_ROW_PADDING', Math.ceil(value / getters.getRowHeight / 2))
    dispatch('visibleByScrollTop')
  },
  setAddRowHover({ commit }, value) {
    commit('SET_ADD_ROW_HOVER', value)
  },
  setSelectedCell({ commit }, { rowId, fieldId }) {
    commit('SET_SELECTED_CELL', { rowId, fieldId })
  },
  setMultiSelectHolding({ commit }, value) {
    commit('SET_MULTISELECT_HOLDING', value)
  },
  setMultiSelectActive({ commit }, value) {
    commit('SET_MULTISELECT_ACTIVE', value)
  },
  clearAndDisableMultiSelect({ commit }) {
    commit('CLEAR_MULTISELECT')
    commit('SET_MULTISELECT_ACTIVE', false)
  },
  multiSelectStart({ getters, commit }, { rowId, fieldIndex }) {
    commit('CLEAR_MULTISELECT')

    const rowIndex = getters.getRowIndexById(rowId)
    // Set the head and tail index to highlight the first cell
    commit('UPDATE_MULTISELECT', { position: 'head', rowIndex, fieldIndex })
    commit('UPDATE_MULTISELECT', { position: 'tail', rowIndex, fieldIndex })

    // Update the store to show that the mouse is being held for multi-select
    commit('SET_MULTISELECT_HOLDING', true)
    // Do not enable multi-select if only a single cell is selected
    commit('SET_MULTISELECT_ACTIVE', false)
  },
  multiSelectHold({ getters, commit }, { rowId, fieldIndex }) {
    if (getters.isMultiSelectHolding) {
      // Unselect single cell
      commit('SET_SELECTED_CELL', { rowId: -1, fieldId: -1 })

      commit('UPDATE_MULTISELECT', {
        position: 'tail',
        rowIndex: getters.getRowIndexById(rowId),
        fieldIndex,
      })

      commit('SET_MULTISELECT_ACTIVE', true)
    }
  },
  /**
   * Returns the fields and rows necessaries to extract data from the selection.
   * It only contains the rows and fields selected by the multiple select.
   * If one or more rows are not in the buffer, they are fetched from the backend.
   */
  async getCurrentSelection(
    { dispatch, getters, commit },
    { fields, type = 'text/plain' }
  ) {
    if (!getters.isMultiSelectActive) {
      return
    }
    const [minFieldIndex, maxFieldIndex] =
      getters.getMultiSelectFieldIndexSorted

    let rows = []
    fields = fields.slice(minFieldIndex, maxFieldIndex + 1)

    if (getters.areMultiSelectRowsWithinBuffer) {
      rows = getters.getSelectedRows
    } else {
      // Fetch rows from backend
      const [minRowIndex, maxRowIndex] = getters.getMultiSelectRowIndexSorted
      const limit = maxRowIndex - minRowIndex + 1
      rows = await dispatch('fetchRowsByIndex', {
        startIndex: minRowIndex,
        limit,
        fields,
      })
    }

    return [fields, rows]
  },
  /**
   * This function is called if a user attempts to access rows that are
   * no longer in the row buffer and need to be fetched from the backend.
   * A user can select some or all fields in a row, and only those fields
   * will be returned.
   */
  async fetchRowsByIndex(
    { getters, rootGetters },
    { startIndex, limit, fields, excludeFields }
  ) {
    if (fields !== undefined) {
      fields = fields.map((field) => `field_${field.id}`)
    }
    if (excludeFields !== undefined) {
      excludeFields = excludeFields.map((field) => `field_${field.id}`)
    }

    const gridId = getters.getLastGridId
    const { data } = await GridService(this.$client).fetchRows({
      gridId,
      offset: startIndex,
      limit,
      search: getters.getServerSearchTerm,
      publicUrl: rootGetters['page/view/public/getIsPublic'],
      publicAuthToken: rootGetters['page/view/public/getAuthToken'],
      orderBy: getOrderBy(rootGetters, getters.getLastGridId),
      filters: getFilters(rootGetters, getters.getLastGridId),
      includeFields: fields,
      excludeFields,
    })
    return data.results
  },
  setRowHover({ commit }, { row, value }) {
    commit('SET_ROW_HOVER', { row, value })
  },
  /**
   * Adds a field with a provided value to the rows in memory.
   */
  addField({ commit }, { field, value = null }) {
    commit('ADD_FIELD_TO_ROWS_IN_BUFFER', { field, value })
  },
  /**
   * Adds a field to the list of selected fields of a row. We use this to indicate
   * if a row is selected or not.
   */
  addRowSelectedBy({ commit }, { row, field }) {
    commit('ADD_ROW_SELECTED_BY', { row, fieldId: field.id })
  },
  /**
   * Removes a field from the list of selected fields of a row. We use this to
   * indicate if a row is selected or not. If the field is not selected anymore
   * and it does not match the filters it can be removed from the store.
   */
  removeRowSelectedBy(
    { dispatch, commit },
    { grid, row, field, fields, getScrollTop }
  ) {
    commit('REMOVE_ROW_SELECTED_BY', { row, fieldId: field.id })
    dispatch('refreshRow', { grid, row, fields, getScrollTop })
  },
  /**
   * Called when the user wants to create a new row. Optionally a `before` row
   * object can be provided which will forcefully add the row before that row. If no
   * `before` is provided, the row will be added last.
   */
  async createNewRow(
    { commit, getters, dispatch },
    { view, table, fields, values = {}, before = null }
  ) {
    // Fill values with empty values of field if they are not provided
    fields.forEach((field) => {
      const name = `field_${field.id}`
      const fieldType = this.$registry.get('field', field._.type.type)

      if (!(name in values)) {
        values[name] = fieldType.getNewRowValue(field)
      }
    })

    // Fill the not provided values with the empty value of the field type so we can
    // immediately commit the created row to the state.
    const preparedRow = prepareRowForRequest(values, fields, this.$registry)

    // If before is not provided, then the row is added last. Because we don't know
    // the total amount of rows in the table, we are going to add find the highest
    // existing order in the buffer and increase that by one.
    let order = getters.getHighestOrder
      .integerValue(BigNumber.ROUND_CEIL)
      .plus('1')
      .toString()
    let index = getters.getBufferEndIndex
    if (before !== null) {
      // If the row has been placed before another row we can specifically insert to
      // the row at a calculated index.
      const change = new BigNumber('0.00000000000000000001')
      order = new BigNumber(before.order).minus(change).toString()
      index = getters.getAllRows.findIndex((r) => r.id === before.id)
    }

    // Populate the row and set the loading state to indicate that the row has not
    // yet been added.
    const row = Object.assign({}, values)
    populateRow(row)
    row.id = uuid()
    row.order = order
    row._.loading = true

    commit('INSERT_NEW_ROW_IN_BUFFER_AT_INDEX', { row, index })
    dispatch('visibleByScrollTop')

    try {
      const { data } = await RowService(this.$client).create(
        table.id,
        preparedRow,
        before !== null ? before.id : null
      )
      commit('FINALIZE_ROW_IN_BUFFER', {
        oldId: row.id,
        id: data.id,
        order: data.order,
        values: data,
      })
      dispatch('onRowChange', { view, row, fields })
      dispatch('fetchAllFieldAggregationData', {
        view,
      })
    } catch (error) {
      commit('DELETE_ROW_IN_BUFFER', row)
      throw error
    }
  },
  /**
   * Called after a new row has been created, which could be by the user or via
   * another channel. It will only add the row if it belongs inside the views and it
   * also makes sure that row will be inserted at the correct position.
   */
  createdNewRow(
    { commit, getters, dispatch },
    { view, fields, values, metadata }
  ) {
    const row = clone(values)
    populateRow(row, metadata)

    // Check if the row belongs into the current view by checking if it matches the
    // filters and search.
    dispatch('updateMatchFilters', { view, row, fields })
    dispatch('updateSearchMatchesForRow', { row, fields })

    // If the row does not match the filters or the search then we don't have to add
    // it at all.
    if (!row._.matchFilters || !row._.matchSearch) {
      return
    }

    // Now that we know that the row applies to the filters, which means it belongs
    // in this view, we need to estimate what position it has in the table.
    const allRowsCopy = clone(getters.getAllRows)
    allRowsCopy.push(row)
    const sortFunction = getRowSortFunction(
      this.$registry,
      view.sortings,
      fields
    )
    allRowsCopy.sort(sortFunction)
    const index = allRowsCopy.findIndex((r) => r.id === row.id)

    const isFirst = index === 0
    const isLast = index === allRowsCopy.length - 1

    if (
      // All of these scenario's mean that the row belongs in the buffer that
      // we have loaded currently.
      (isFirst && getters.getBufferStartIndex === 0) ||
      (isLast && getters.getBufferEndIndex === getters.getCount) ||
      (index > 0 && index < allRowsCopy.length - 1)
    ) {
      commit('INSERT_NEW_ROW_IN_BUFFER_AT_INDEX', { row, index })
    } else {
      if (isFirst) {
        // Because the row has been added before the our buffer, we need know that the
        // buffer start index has increased by one.
        commit('SET_BUFFER_START_INDEX', getters.getBufferStartIndex + 1)
      }
      // The row has been added outside of the buffer, so we can safely increase the
      // count.
      commit('SET_COUNT', getters.getCount + 1)
    }
  },
  /**
   * Moves an existing row to the position before the provided before row. It will
   * update the order and makes sure that the row is inserted in the correct place.
   * A call to the backend will also be made to update the order persistent.
   */
  async moveRow(
    { commit, dispatch, getters },
    { table, grid, fields, getScrollTop, row, before = null }
  ) {
    const oldOrder = row.order

    // If before is not provided, then the row is added last. Because we don't know
    // the total amount of rows in the table, we are going to add find the highest
    // existing order in the buffer and increase that by one.
    let order = getters.getHighestOrder
      .integerValue(BigNumber.ROUND_CEIL)
      .plus('1')
      .toString()
    if (before !== null) {
      // If the row has been placed before another row we can specifically insert to
      // the row at a calculated index.
      const change = new BigNumber('0.00000000000000000001')
      order = new BigNumber(before.order).minus(change).toString()
    }

    // In order to make changes feel really fast, we optimistically
    // updated all the field values that provide a onRowMove function
    const fieldsToCallOnRowMove = fields
    const optimisticFieldValues = {}
    const valuesBeforeOptimisticUpdate = {}

    fieldsToCallOnRowMove.forEach((field) => {
      const fieldType = this.$registry.get('field', field._.type.type)
      const fieldID = `field_${field.id}`
      const currentFieldValue = row[fieldID]
      const fieldValue = fieldType.onRowMove(
        row,
        order,
        oldOrder,
        field,
        currentFieldValue
      )
      if (currentFieldValue !== fieldValue) {
        optimisticFieldValues[fieldID] = fieldValue
        valuesBeforeOptimisticUpdate[fieldID] = currentFieldValue
      }
    })

    dispatch('updatedExistingRow', {
      view: grid,
      fields,
      row,
      values: { order, ...optimisticFieldValues },
    })

    try {
      const { data } = await RowService(this.$client).move(
        table.id,
        row.id,
        before !== null ? before.id : null
      )
      // Use the return value to update the moved row with values from
      // the backend
      commit('UPDATE_ROW_IN_BUFFER', { row, values: data })
      if (before === null) {
        // Not having a before means that the row was moved to the end and because
        // that order was just an estimation, we want to update it with the real
        // order, otherwise there could be order conflicts in the future.
        commit('UPDATE_ROW_IN_BUFFER', { row, values: { order: data.order } })
      }
      dispatch('fetchByScrollTopDelayed', {
        scrollTop: getScrollTop(),
        fields,
      })
      dispatch('fetchAllFieldAggregationData', { view: grid })
    } catch (error) {
      dispatch('updatedExistingRow', {
        view: grid,
        fields,
        row,
        values: { order: oldOrder, ...valuesBeforeOptimisticUpdate },
      })
      throw error
    }
  },
  /**
   * Updates a grid view field value. It will immediately be updated in the store
   * and only if the change request fails it will reverted to give a faster
   * experience for the user.
   */
  async updateRowValue(
    { commit, dispatch },
    { table, view, row, field, fields, value, oldValue }
  ) {
    // Immediately updated the store with the updated row field
    // value.
    commit('UPDATE_ROW_FIELD_VALUE', { row, field, value })

    const optimisticFieldValues = {}
    const valuesBeforeOptimisticUpdate = {}

    // Store the before value of the field that gets updated
    // in case we need to rollback changes
    valuesBeforeOptimisticUpdate[`field_${field.id}`] = oldValue

    let fieldsToCallOnRowChange = fields

    // We already added the updated field values to the store
    // so we can remove the field from our fieldsToCallOnRowChange
    fieldsToCallOnRowChange = fieldsToCallOnRowChange.filter((el) => {
      return el.id !== field.id
    })

    fieldsToCallOnRowChange.forEach((fieldToCall) => {
      const fieldType = this.$registry.get('field', fieldToCall._.type.type)
      const fieldID = `field_${fieldToCall.id}`
      const currentFieldValue = row[fieldID]
      const optimisticFieldValue = fieldType.onRowChange(
        row,
        fieldToCall,
        currentFieldValue
      )

      if (currentFieldValue !== optimisticFieldValue) {
        optimisticFieldValues[fieldID] = optimisticFieldValue
        valuesBeforeOptimisticUpdate[fieldID] = currentFieldValue
      }
    })
    commit('UPDATE_ROW_IN_BUFFER', {
      row,
      values: { ...optimisticFieldValues },
    })
    dispatch('onRowChange', { view, row, fields })

    const fieldType = this.$registry.get('field', field._.type.type)
    const newValue = fieldType.prepareValueForUpdate(field, value)
    const values = {}
    values[`field_${field.id}`] = newValue

    try {
      const updatedRow = await RowService(this.$client).update(
        table.id,
        row.id,
        values
      )
      commit('UPDATE_ROW_IN_BUFFER', { row, values: updatedRow.data })
      dispatch('onRowChange', { view, row, fields })
      dispatch('fetchAllFieldAggregationData', {
        view,
      })
    } catch (error) {
      commit('UPDATE_ROW_IN_BUFFER', {
        row,
        values: { ...valuesBeforeOptimisticUpdate },
      })

      dispatch('onRowChange', { view, row, fields })
      throw error
    }
  },
  /**
   * Set the multiple select indexes using the row and field head and tail indexes.
   */
  setMultipleSelect(
    { commit },
    { rowHeadIndex, fieldHeadIndex, rowTailIndex, fieldTailIndex }
  ) {
    commit('UPDATE_MULTISELECT', {
      position: 'head',
      rowIndex: rowHeadIndex,
      fieldIndex: fieldHeadIndex,
    })
    commit('UPDATE_MULTISELECT', {
      position: 'tail',
      rowIndex: rowTailIndex,
      fieldIndex: fieldTailIndex,
    })
    commit('SET_MULTISELECT_ACTIVE', true)
    // Unselect a single selected cell because we've just updated the multiple
    // selected and we don't want that to conflict.
    commit('SET_SELECTED_CELL', { rowId: -1, fieldId: -1 })
  },
  /**
   * This action is used by the grid view to change multiple cells when pasting
   * multiple values. It figures out which cells need to be changed, makes a request
   * to the backend and updates the affected rows in the store.
   */
  async updateDataIntoCells(
    { getters, commit, dispatch },
    {
      table,
      view,
      fields,
      getScrollTop,
      textData,
      jsonData,
      rowIndex,
      fieldIndex,
    }
  ) {
    // If the origin row and field index are not provided, we need to use the
    // head indexes of the multiple select.
    const rowHeadIndex = rowIndex ?? getters.getMultiSelectHeadRowIndex
    const fieldHeadIndex = fieldIndex ?? getters.getMultiSelectHeadFieldIndex

    // Based on the data, we can figure out in which cells we must paste. Here we find
    // the maximum tail indexes.
    const rowTailIndex =
      Math.min(getters.getCount, rowHeadIndex + textData.length) - 1
    const fieldTailIndex =
      Math.min(fields.length, fieldHeadIndex + textData[0].length) - 1

    // Expand the selection of the multiple select to the cells that we're going to
    // paste in, so the user can see which values have been updated. This is because
    // it could be that there are more or less values in the clipboard compared to
    // what was originally selected.
    await dispatch('setMultipleSelect', {
      rowHeadIndex,
      fieldHeadIndex,
      rowTailIndex,
      fieldTailIndex,
    })

    // Figure out which rows are already in the buffered and temporarily store them
    // in an array.
    const fieldsInOrder = fields.slice(fieldHeadIndex, fieldTailIndex + 1)
    let rowsInOrder = getters.getAllRows.slice(
      rowHeadIndex - getters.getBufferStartIndex,
      rowTailIndex + 1 - getters.getBufferStartIndex
    )

    // Check if there are fields that can be updated. If there aren't any fields,
    // maybe because the provided index is outside of the available fields or
    // because there are only read only fields, we don't want to do anything.
    const writeFields = fieldsInOrder.filter(
      (field) => !field._.type.isReadOnly
    )
    if (writeFields.length === 0) {
      return
    }

    // Calculate if there are rows outside of the buffer that need to be fetched and
    // prepended or appended to the `rowsInOrder`
    const startIndex = rowHeadIndex + rowsInOrder.length
    const limit = rowTailIndex - rowHeadIndex - rowsInOrder.length + 1
    if (limit > 0) {
      const rowsNotInBuffer = await dispatch('fetchRowsByIndex', {
        startIndex,
        limit,
      })
      // Depends on whether the missing rows are before or after the buffer.
      rowsInOrder =
        startIndex < getters.getBufferStartIndex
          ? [...rowsNotInBuffer, ...rowsInOrder]
          : [...rowsInOrder, ...rowsNotInBuffer]
    }

    // Create a copy of the existing (old) rows, which are needed to create the
    // comparison when checking if the rows still matches the filters and position.
    const oldRowsInOrder = clone(rowsInOrder)
    // Prepare the values that must be send to the server.
    const valuesForUpdate = []
    // Prepare the values for update and update the row objects.

    rowsInOrder.forEach((row, rowIndex) => {
      valuesForUpdate[rowIndex] = { id: row.id }

      fieldsInOrder.forEach((field, fieldIndex) => {
        // We can't pre-filter because we need the correct filter index.
        if (field._.type.isReadOnly) {
          return
        }

        const fieldId = `field_${field.id}`
        const textValue = textData[rowIndex][fieldIndex]
        const jsonValue =
          jsonData !== null ? jsonData[rowIndex][fieldIndex] : undefined

        const fieldType = this.$registry.get('field', field.type)
        const preparedValue = fieldType.prepareValueForPaste(
          field,
          textValue,
          jsonValue
        )
        const newValue = fieldType.prepareValueForUpdate(field, preparedValue)
        valuesForUpdate[rowIndex][fieldId] = newValue
      })
    })

    // We don't have to update the rows in the buffer before the request is being made
    // because we're showing a loading animation to the user indicating that the
    // rows are being updated.
    const { data: responseData } = await RowService(this.$client).batchUpdate(
      table.id,
      valuesForUpdate
    )
    const updatedRows = responseData.items

    // Loop over the old rows, find the matching updated row and update them in the
    // buffer accordingly.
    for (const row of oldRowsInOrder) {
      // The values are the updated row returned by the response.
      const values = updatedRows.find((updatedRow) => updatedRow.id === row.id)
      // Calling the updatedExistingRow will automatically remove the row from the
      // view if it doesn't matter the filters anymore and it will also be moved to
      // the right position if changed.
      await dispatch('updatedExistingRow', {
        view,
        fields,
        row,
        values,
      })
    }

    // Must be called because rows could have been removed or moved to a different
    // position and we might need to fetch missing rows.
    await dispatch('fetchByScrollTopDelayed', {
      scrollTop: getScrollTop(),
      fields,
    })
    dispatch('fetchAllFieldAggregationData', { view })
  },
  /**
   * Called after an existing row has been updated, which could be by the user or
   * via another channel. It will make sure that the row has the correct position or
   * that is will be deleted or created depending if was already in the view.
   */
  updatedExistingRow(
    { commit, getters, dispatch },
    { view, fields, row, values, metadata }
  ) {
    const oldRow = clone(row)
    const newRow = Object.assign(clone(row), values)
    populateRow(oldRow, metadata)
    populateRow(newRow, metadata)

    dispatch('updateMatchFilters', { view, row: oldRow, fields })
    dispatch('updateSearchMatchesForRow', { row: oldRow, fields })

    dispatch('updateMatchFilters', { view, row: newRow, fields })
    dispatch('updateSearchMatchesForRow', { row: newRow, fields })

    const oldRowExists = oldRow._.matchFilters && oldRow._.matchSearch
    const newRowExists = newRow._.matchFilters && newRow._.matchSearch

    if (oldRowExists && !newRowExists) {
      dispatch('deletedExistingRow', { view, fields, row })
    } else if (!oldRowExists && newRowExists) {
      dispatch('createdNewRow', {
        view,
        fields,
        values: newRow,
        metadata,
      })
    } else if (oldRowExists && newRowExists) {
      // If the new order already exists in the buffer and is not the row that has
      // been updated, we need to decrease all the other orders, otherwise we could
      // have duplicate orders.
      if (
        getters.getAllRows.findIndex(
          (r) => r.id !== newRow.id && r.order === newRow.order
        ) > -1
      ) {
        commit('DECREASE_ORDERS_IN_BUFFER_LOWER_THAN', newRow.order)
      }

      // Figure out if the row is currently in the buffer.
      const sortFunction = getRowSortFunction(
        this.$registry,
        view.sortings,
        fields
      )
      const allRows = getters.getAllRows
      const index = allRows.findIndex((r) => r.id === row.id)
      const oldIsFirst = index === 0
      const oldIsLast = index === allRows.length - 1
      const oldRowInBuffer =
        (oldIsFirst && getters.getBufferStartIndex === 0) ||
        (oldIsLast && getters.getBufferEndIndex === getters.getCount) ||
        (index > 0 && index < allRows.length - 1)

      if (oldRowInBuffer) {
        // If the old row is inside the buffer at a known position.
        commit('UPDATE_ROW_IN_BUFFER', { row, values, metadata })
        commit('SET_BUFFER_LIMIT', getters.getBufferLimit - 1)
      } else if (oldIsFirst) {
        // If the old row exists in the buffer, but is at the before position.
        commit('DELETE_ROW_IN_BUFFER_WITHOUT_UPDATE', row)
        commit('SET_BUFFER_LIMIT', getters.getBufferLimit - 1)
      } else if (oldIsLast) {
        // If the old row exists in the buffer, bit is at the after position.
        commit('DELETE_ROW_IN_BUFFER_WITHOUT_UPDATE', row)
        commit('SET_BUFFER_LIMIT', getters.getBufferLimit - 1)
      } else {
        // The row does not exist in the buffer, so we need to check if it is before
        // or after the buffer.
        const allRowsCopy = clone(getters.getAllRows)
        const oldRowIndex = allRowsCopy.findIndex((r) => r.id === oldRow.id)
        if (oldRowIndex > -1) {
          allRowsCopy.splice(oldRowIndex, 1)
        }
        allRowsCopy.push(oldRow)
        allRowsCopy.sort(sortFunction)
        const oldIndex = allRowsCopy.findIndex((r) => r.id === newRow.id)
        if (oldIndex === 0) {
          // If the old row is before the buffer.
          commit('SET_BUFFER_START_INDEX', getters.getBufferStartIndex - 1)
        }
      }

      // Calculate what the new index should be.
      const allRowsCopy = clone(getters.getAllRows)
      const oldRowIndex = allRowsCopy.findIndex((r) => r.id === oldRow.id)
      if (oldRowIndex > -1) {
        allRowsCopy.splice(oldRowIndex, 1)
      }
      allRowsCopy.push(newRow)
      allRowsCopy.sort(sortFunction)
      const newIndex = allRowsCopy.findIndex((r) => r.id === newRow.id)
      const newIsFirst = newIndex === 0
      const newIsLast = newIndex === allRowsCopy.length - 1
      const newRowInBuffer =
        (newIsFirst && getters.getBufferStartIndex === 0) ||
        (newIsLast && getters.getBufferEndIndex === getters.getCount - 1) ||
        (newIndex > 0 && newIndex < allRowsCopy.length - 1)

      if (oldRowInBuffer && newRowInBuffer) {
        // If the old row and the new row are in the buffer.
        if (index !== newIndex) {
          commit('MOVE_EXISTING_ROW_IN_BUFFER', {
            row: oldRow,
            index: newIndex,
          })
        }
        commit('SET_BUFFER_LIMIT', getters.getBufferLimit + 1)
      } else if (newRowInBuffer) {
        // If the new row should be in the buffer, but wasn't.
        commit('INSERT_EXISTING_ROW_IN_BUFFER_AT_INDEX', {
          row: newRow,
          index: newIndex,
        })
        commit('SET_BUFFER_LIMIT', getters.getBufferLimit + 1)
      } else if (newIsFirst) {
        // If the new row is before the buffer.
        commit('SET_BUFFER_START_INDEX', getters.getBufferStartIndex + 1)
      }

      // If the row as in the old buffer, but ended up at the first/before or
      // last/after position. This means that we can't know for sure the row should
      // be in the buffer, so it is removed from it.
      if (oldRowInBuffer && !newRowInBuffer && (newIsFirst || newIsLast)) {
        commit('DELETE_ROW_IN_BUFFER_WITHOUT_UPDATE', row)
      }
    }
  },
  /**
   * Called when the user wants to delete an existing row in the table.
   */
  async deleteExistingRow(
    { commit, dispatch, getters },
    { table, view, row, fields, getScrollTop }
  ) {
    commit('SET_ROW_LOADING', { row, value: true })

    try {
      await RowService(this.$client).delete(table.id, row.id)
      await dispatch('deletedExistingRow', {
        view,
        fields,
        row,
        getScrollTop,
      })
      await dispatch('fetchByScrollTopDelayed', {
        scrollTop: getScrollTop(),
        fields,
      })
      dispatch('fetchAllFieldAggregationData', { view })
    } catch (error) {
      commit('SET_ROW_LOADING', { row, value: false })
      throw error
    }
  },
  /**
   * Attempt to delete all multi-selected rows.
   */
  async deleteSelectedRows(
    { dispatch, getters },
    { table, view, fields, getScrollTop }
  ) {
    if (!getters.isMultiSelectActive) {
      return
    }
    let rows = []
    if (getters.areMultiSelectRowsWithinBuffer) {
      rows = getters.getSelectedRows
    } else {
      // Rows not in buffer, fetch from backend
      const [minRowIndex, maxRowIndex] = getters.getMultiSelectRowIndexSorted
      const limit = maxRowIndex - minRowIndex + 1

      rows = await dispatch('fetchRowsByIndex', {
        startIndex: minRowIndex,
        limit,
        includeFields: fields,
      })
    }
    const rowIdsToDelete = rows.map((r) => r.id)
    await RowService(this.$client).batchDelete(table.id, rowIdsToDelete)

    for (const row of rows) {
      await dispatch('deletedExistingRow', {
        view,
        fields,
        row,
        getScrollTop,
      })
    }
    dispatch('clearAndDisableMultiSelect', { view })
    await dispatch('fetchByScrollTopDelayed', {
      scrollTop: getScrollTop(),
      fields,
    })
    dispatch('fetchAllFieldAggregationData', { view })
  },
  /**
   * Called after an existing row has been deleted, which could be by the user or
   * via another channel.
   */
  deletedExistingRow({ commit, getters, dispatch }, { view, fields, row }) {
    row = clone(row)
    populateRow(row)

    // Check if that row was visible in the view.
    dispatch('updateMatchFilters', { view, row, fields })
    dispatch('updateSearchMatchesForRow', { row, fields })

    // If the row does not match the filters or the search then did not exist in the
    // view, so we don't have to do anything.
    if (!row._.matchFilters || !row._.matchSearch) {
      return
    }

    // Now that we know for sure that the row belongs in the view, we need to figure
    // out if is before, inside or after the buffered results.
    const allRowsCopy = clone(getters.getAllRows)
    const exists = allRowsCopy.findIndex((r) => r.id === row.id) > -1

    // If the row is already in the buffer, it can be removed via the
    // `DELETE_ROW_IN_BUFFER` commit, which removes it and changes the buffer state
    // accordingly.
    if (exists) {
      commit('DELETE_ROW_IN_BUFFER', row)
      return
    }

    // Otherwise we have to calculate was before or after the current buffer.
    allRowsCopy.push(row)
    const sortFunction = getRowSortFunction(
      this.$registry,
      view.sortings,
      fields
    )
    allRowsCopy.sort(sortFunction)
    const index = allRowsCopy.findIndex((r) => r.id === row.id)

    // If the row is at position 0, it means that the row existed before the buffer,
    // which means the buffer start index has decreased.
    if (index === 0) {
      commit('SET_BUFFER_START_INDEX', getters.getBufferStartIndex - 1)
    }

    // Regardless of where the
    commit('SET_COUNT', getters.getCount - 1)
  },
  /**
   * Triggered when a row has been changed, or has a pending change in the provided
   * overrides.
   */
  onRowChange({ dispatch }, { view, row, fields, overrides = {} }) {
    dispatch('updateMatchFilters', { view, row, fields, overrides })
    dispatch('updateMatchSortings', { view, row, fields, overrides })
    dispatch('updateSearchMatchesForRow', { row, fields, overrides })
  },
  /**
   * Checks if the given row still matches the given view filters. The row's
   * matchFilters value is updated accordingly. It is also possible to provide some
   * override values that not actually belong to the row to do some preliminary checks.
   */
  updateMatchFilters({ commit }, { view, row, fields, overrides = {} }) {
    const values = JSON.parse(JSON.stringify(row))
    Object.assign(values, overrides)

    // The value is always valid if the filters are disabled.
    const matches = view.filters_disabled
      ? true
      : matchSearchFilters(
          this.$registry,
          view.filter_type,
          view.filters,
          fields,
          values
        )
    commit('SET_ROW_MATCH_FILTERS', { row, value: matches })
  },
  /**
   * Changes the current search parameters if provided and optionally refreshes which
   * cells match the new search parameters by updating every rows row._.matchSearch and
   * row._.fieldSearchMatches attributes.
   */
  updateSearch(
    { commit, dispatch, getters, state },
    {
      fields,
      activeSearchTerm = state.activeSearchTerm,
      hideRowsNotMatchingSearch = state.hideRowsNotMatchingSearch,
      refreshMatchesOnClient = true,
    }
  ) {
    commit('SET_SEARCH', { activeSearchTerm, hideRowsNotMatchingSearch })
    if (refreshMatchesOnClient) {
      getters.getAllRows.forEach((row) =>
        dispatch('updateSearchMatchesForRow', {
          row,
          fields,
          forced: true,
        })
      )
    }
  },
  /**
   * Updates a single row's row._.matchSearch and row._.fieldSearchMatches based on the
   * current search parameters and row data. Overrides can be provided which can be used
   * to override a row's field values when checking if they match the search parameters.
   */
  updateSearchMatchesForRow(
    { commit, getters, rootGetters },
    { row, fields = null, overrides, forced = false }
  ) {
    // Avoid computing search on table loading
    if (getters.getActiveSearchTerm || forced) {
      const rowSearchMatches = calculateSingleRowSearchMatches(
        row,
        getters.getActiveSearchTerm,
        getters.isHidingRowsNotMatchingSearch,
        fields,
        this.$registry,
        overrides
      )

      commit('SET_ROW_SEARCH_MATCHES', rowSearchMatches)
    }
  },
  /**
   * Checks if the given row index is still the same. The row's matchSortings value is
   * updated accordingly. It is also possible to provide some override values that not
   * actually belong to the row to do some preliminary checks.
   */
  updateMatchSortings(
    { commit, getters },
    { view, row, fields, overrides = {} }
  ) {
    const values = clone(row)
    Object.assign(values, overrides)

    const allRows = getters.getAllRows
    const currentIndex = getters.getAllRows.findIndex((r) => r.id === row.id)
    const sortedRows = clone(allRows)
    sortedRows[currentIndex] = values
    sortedRows.sort(getRowSortFunction(this.$registry, view.sortings, fields))
    const newIndex = sortedRows.findIndex((r) => r.id === row.id)

    commit('SET_ROW_MATCH_SORTINGS', { row, value: currentIndex === newIndex })
  },
  /**
   * The row is going to be removed or repositioned if the matchFilters and
   * matchSortings state is false. It will make the state correct.
   */
  async refreshRow(
    { dispatch, commit, getters },
    { grid, row, fields, getScrollTop }
  ) {
    const rowShouldBeHidden = !row._.matchFilters || !row._.matchSearch
    if (row._.selectedBy.length === 0 && rowShouldBeHidden) {
      commit('DELETE_ROW_IN_BUFFER', row)
    } else if (row._.selectedBy.length === 0 && !row._.matchSortings) {
      await dispatch('updatedExistingRow', {
        view: grid,
        fields,
        row,
        values: row,
      })
      commit('SET_ROW_MATCH_SORTINGS', { row, value: true })
    }
    dispatch('fetchByScrollTopDelayed', {
      scrollTop: getScrollTop(),
      fields,
    })
  },
  updateRowMetadata(
    { commit, getters, dispatch },
    { tableId, rowId, rowMetadataType, updateFunction }
  ) {
    const row = getters.getRow(rowId)
    if (row) {
      commit('UPDATE_ROW_METADATA', { row, rowMetadataType, updateFunction })
    }
  },
  /**
   * Clears the values of all multi-selected cells by updating them to their null values.
   */
  async clearValuesFromMultipleCellSelection(
    { getters, dispatch },
    { table, view, fields, getScrollTop }
  ) {
    const [minFieldIndex, maxFieldIndex] =
      getters.getMultiSelectFieldIndexSorted

    const [minRowIndex, maxRowIndex] = getters.getMultiSelectRowIndexSorted
    const numberOfRowsSelected = maxRowIndex - minRowIndex + 1

    const selectedFields = fields.slice(minFieldIndex, maxFieldIndex + 1)

    // Get the empty value for each selected field
    const emptyValues = selectedFields.map((field) =>
      this.$registry.get('field', field.type).getEmptyValue(field)
    )

    // Copy the empty value array once for each row selected
    const data = []
    for (let index = 0; index < numberOfRowsSelected; index++) {
      data.push(emptyValues)
    }

    await dispatch('updateDataIntoCells', {
      table,
      view,
      fields,
      getScrollTop,
      textData: data,
      rowIndex: minRowIndex,
      fieldIndex: minFieldIndex,
    })
  },
}

export const getters = {
  isLoaded(state) {
    return state.loaded
  },
  getLastGridId(state) {
    return state.lastGridId
  },
  getCount(state) {
    return state.count
  },
  getRowHeight(state) {
    return state.rowHeight
  },
  getRowsTop(state) {
    return state.rowsTop
  },
  getRowsLength(state) {
    return state.rows.length
  },
  getPlaceholderHeight(state) {
    return state.count * state.rowHeight
  },
  getRowPadding(state) {
    return state.rowPadding
  },
  getAllRows(state) {
    return state.rows
  },
  getRow: (state) => (id) => {
    return state.rows.find((row) => row.id === id)
  },
  getRows(state) {
    return state.rows.slice(state.rowsStartIndex, state.rowsEndIndex)
  },
  getRowsStartIndex(state) {
    return state.rowsStartIndex
  },
  getRowsEndIndex(state) {
    return state.rowsEndIndex
  },
  getBufferRequestSize(state) {
    return state.bufferRequestSize
  },
  getBufferStartIndex(state) {
    return state.bufferStartIndex
  },
  getBufferEndIndex(state) {
    return state.bufferStartIndex + state.bufferLimit
  },
  getBufferLimit(state) {
    return state.bufferLimit
  },
  getScrollTop(state) {
    return state.scrollTop
  },
  getWindowHeight(state) {
    return state.windowHeight
  },
  getAllFieldOptions(state) {
    return state.fieldOptions
  },
  isFirst: (state) => (id) => {
    const index = state.rows.findIndex((row) => row.id === id)
    return index === 0
  },
  isLast: (state) => (id) => {
    const index = state.rows.findIndex((row) => row.id === id)
    return index === state.rows.length - 1
  },
  getAddRowHover(state) {
    return state.addRowHover
  },
  getActiveSearchTerm(state) {
    return state.activeSearchTerm
  },
  isHidingRowsNotMatchingSearch(state) {
    return state.hideRowsNotMatchingSearch
  },
  getServerSearchTerm(state) {
    return state.hideRowsNotMatchingSearch ? state.activeSearchTerm : false
  },
  getHighestOrder(state) {
    let order = new BigNumber('0.00000000000000000000')
    state.rows.forEach((r) => {
      const rOrder = new BigNumber(r.order)
      if (rOrder.isGreaterThan(order)) {
        order = rOrder
      }
    })
    return order
  },
  isMultiSelectActive(state) {
    return state.multiSelectActive
  },
  isMultiSelectHolding(state) {
    return state.multiSelectHolding
  },
  getMultiSelectRowIndexSorted(state) {
    return [
      Math.min(state.multiSelectHeadRowIndex, state.multiSelectTailRowIndex),
      Math.max(state.multiSelectHeadRowIndex, state.multiSelectTailRowIndex),
    ]
  },
  getMultiSelectFieldIndexSorted(state) {
    return [
      Math.min(
        state.multiSelectHeadFieldIndex,
        state.multiSelectTailFieldIndex
      ),
      Math.max(
        state.multiSelectHeadFieldIndex,
        state.multiSelectTailFieldIndex
      ),
    ]
  },
  getMultiSelectHeadFieldIndex(state) {
    // Return the leftmost
    return Math.min(
      state.multiSelectHeadFieldIndex,
      state.multiSelectTailFieldIndex
    )
  },
  getMultiSelectHeadRowIndex(state) {
    // Return the topmost
    return Math.min(
      state.multiSelectHeadRowIndex,
      state.multiSelectTailRowIndex
    )
  },
  // Get the index of a row given it's row id.
  // This will calculate the row index from the current buffer position and offset.
  getRowIndexById: (state, getters) => (rowId) => {
    const bufferIndex = state.rows.findIndex((r) => r.id === rowId)
    if (bufferIndex !== -1) {
      return getters.getBufferStartIndex + bufferIndex
    }
    return -1
  },
  // Check if all the multi-select rows are within the row buffer
  areMultiSelectRowsWithinBuffer(state, getters) {
    const [minRow, maxRow] = getters.getMultiSelectRowIndexSorted

    return (
      minRow >= getters.getBufferStartIndex &&
      maxRow <= getters.getBufferEndIndex
    )
  },
  // Return all rows within a multi-select grid if they are within the current row buffer
  getSelectedRows(state, getters) {
    const [minRow, maxRow] = getters.getMultiSelectRowIndexSorted

    if (getters.areMultiSelectRowsWithinBuffer) {
      return state.rows.slice(
        minRow - state.bufferStartIndex,
        maxRow - state.bufferStartIndex + 1
      )
    }
  },
  getAllFieldAggregationData(state) {
    return state.fieldAggregationData
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
