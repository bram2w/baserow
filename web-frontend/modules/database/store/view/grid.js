import Vue from 'vue'
import axios from 'axios'
import _ from 'lodash'
import BigNumber from 'bignumber.js'

import { uuid } from '@baserow/modules/core/utils/string'
import { clone } from '@baserow/modules/core/utils/object'
import GridService from '@baserow/modules/database/services/view/grid'
import RowService from '@baserow/modules/database/services/row'
import {
  calculateSingleRowSearchMatches,
  getRowSortFunction,
  matchSearchFilters,
} from '@baserow/modules/database/utils/view'
import { RefreshCancelledError } from '@baserow/modules/core/errors'

export function populateRow(row) {
  row._ = {
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

export const state = () => ({
  loading: false,
  loaded: false,
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
  // The last windowHeight when the visibleByScrollTop was called.
  windowHeight: 0,
  // Indicates if the user is hovering over the add row button.
  addRowHover: false,
  // A user provided optional search term which can be used to filter down rows.
  activeSearchTerm: '',
  // If true then the activeSearchTerm will be sent to the server to filter rows
  // entirely out. When false no server filter will be applied and rows which do not
  // have any matching cells will still be displayed.
  hideRowsNotMatchingSearch: true,
})

export const mutations = {
  SET_LOADING(state, value) {
    state.loading = value
  },
  SET_LOADED(state, value) {
    state.loaded = value
  },
  SET_SEARCH(state, { activeSearchTerm, hideRowsNotMatchingSearch }) {
    state.activeSearchTerm = activeSearchTerm
    state.hideRowsNotMatchingSearch = hideRowsNotMatchingSearch
  },
  SET_LAST_GRID_ID(state, gridId) {
    state.lastGridId = gridId
  },
  SET_SCROLL_TOP(state, { scrollTop, windowHeight }) {
    state.scrollTop = scrollTop
    state.windowHeight = windowHeight
  },
  CLEAR_ROWS(state) {
    state.rows = []
    state.rowsTop = 0
    state.bufferStartIndex = 0
    state.bufferEndIndex = 0
    state.bufferLimit = 0
    state.rowsStartIndex = 0
    state.rowsEndIndex = 0
    state.scrollTop = 0
    state.activeSearchTerm = ''
    state.hideRowsNotMatchingSearch = true
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
  /**
   * Inserts a new row at a specific index.
   */
  INSERT_ROW_AT(state, { row, index }) {
    state.count++
    state.bufferLimit++

    const min = new BigNumber(row.order.split('.')[0])
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

    state.rows.splice(index, 0, row)
  },
  SET_ROWS_INDEX(state, { startIndex, endIndex, top }) {
    state.rowsStartIndex = startIndex
    state.rowsEndIndex = endIndex
    state.rowsTop = top
  },
  DELETE_ROW(state, id) {
    const index = state.rows.findIndex((item) => item.id === id)
    if (index !== -1) {
      // A small side effect of the buffered loading is that we don't know for sure if
      // the row exists within the view. So the count might need to be decreased
      // even though the row is not found. Because we don't want to make another call
      // to the backend we only decrease the count if the row is found in the buffer.
      // The count is eventually refreshed when the user scrolls within the view.
      state.count--
      state.bufferLimit--
      state.rows.splice(index, 1)
    }
  },
  DELETE_ROW_MOVED_UP(state, id) {
    const index = state.rows.findIndex((item) => item.id === id)
    if (index !== -1) {
      state.bufferStartIndex++
      state.bufferLimit--
      state.rows.splice(index, 1)
    }
  },
  DELETE_ROW_MOVED_DOWN(state, id) {
    const index = state.rows.findIndex((item) => item.id === id)
    if (index !== -1) {
      state.bufferLimit--
      state.rows.splice(index, 1)
    }
  },
  FINALIZE_ROW(state, { oldId, id, order }) {
    const index = state.rows.findIndex((item) => item.id === oldId)
    if (index !== -1) {
      state.rows[index].id = id
      state.rows[index].order = order
      state.rows[index]._.loading = false
    }
  },
  SET_VALUE(state, { row, field, value }) {
    row[`field_${field.id}`] = value
  },
  UPDATE_ROW(state, { row, values }) {
    _.assign(row, values)
  },
  UPDATE_ROWS(state, { rows }) {
    rows.forEach((newRow) => {
      const row = state.rows.find((row) => row.id === newRow.id)
      if (row !== undefined) {
        _.assign(row, newRow)
      }
    })
  },
  SORT_ROWS(state, sortFunction) {
    state.rows.sort(sortFunction)

    // Because all the rows have been sorted again we can safely assume they are all in
    // the right order again.
    state.rows.forEach((row) => {
      if (!row._.matchSortings) {
        row._.matchSortings = true
      }
    })
  },
  ADD_FIELD(state, { field, value }) {
    const name = `field_${field.id}`
    state.rows.forEach((row) => {
      // We have to use the Vue.set function here to make it reactive immediately.
      // If we don't do this the value in the field components of the grid and modal
      // don't have the correct value and will act strange.
      Vue.set(row, name, value)
    })
  },
  SET_ROW_LOADING(state, { row, value }) {
    row._.loading = value
  },
  REPLACE_ALL_FIELD_OPTIONS(state, fieldOptions) {
    state.fieldOptions = fieldOptions
  },
  UPDATE_ALL_FIELD_OPTIONS(state, fieldOptions) {
    state.fieldOptions = _.merge({}, state.fieldOptions, fieldOptions)
  },
  UPDATE_FIELD_OPTIONS_OF_FIELD(state, { fieldId, values }) {
    if (Object.prototype.hasOwnProperty.call(state.fieldOptions, fieldId)) {
      _.assign(state.fieldOptions[fieldId], values)
    } else {
      state.fieldOptions = _.assign({}, state.fieldOptions, {
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
  SET_ADD_ROW_HOVER(state, value) {
    state.addRowHover = value
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
}

// Contains the timeout needed for the delayed delayed scroll top action.
let fireTimeout = null
// Contains a timestamp of the last fire of the related actions to the delayed
// scroll top action.
let lastFire = null
// Contains the
let lastScrollTop = null
let lastRequest = null
let lastRequestOffset = null
let lastRequestLimit = null
let lastRefreshRequest = null
let lastRefreshRequestSource = null
let lastSource = null

export const actions = {
  /**
   * This action calculates which rows we would like to have in the buffer based on
   * the scroll top offset and the window height. Based on that is calculates which
   * rows we need to fetch compared to what we already have. If we need to fetch
   * anything other then we already have or waiting for a new request will be made.
   */
  fetchByScrollTop(
    { commit, getters, dispatch },
    { gridId, scrollTop, windowHeight, fields, primary }
  ) {
    commit('SET_LAST_GRID_ID', gridId)

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
      // If another request is runnig we need to cancel that one because it won't
      // what we need at the moment.
      if (lastRequest !== null) {
        lastSource.cancel('Canceled in favor of new request')
      }

      // Doing the actual request and remember what we are requesting so we can compare
      // it when making a new request.
      lastRequestOffset = requestOffset
      lastRequestLimit = requestLimit
      lastSource = axios.CancelToken.source()
      lastRequest = GridService(this.$client)
        .fetchRows({
          gridId,
          offset: requestOffset,
          limit: requestLimit,
          cancelToken: lastSource.token,
          search: getters.getServerSearchTerm,
        })
        .then(({ data }) => {
          data.results.forEach((part, index) => {
            populateRow(data.results[index])
          })
          commit('ADD_ROWS', {
            rows: data.results,
            prependToRows: prependToBuffer,
            appendToRows: appendToBuffer,
            count: data.count,
            bufferStartIndex,
            bufferLimit,
          })
          dispatch('visibleByScrollTop', {
            // Somehow we have to explicitly set these values to null.
            scrollTop: null,
            windowHeight: null,
          })
          dispatch('updateSearch', { fields, primary })
          lastRequest = null
        })
        .catch((error) => {
          if (!axios.isCancel(error)) {
            lastRequest = null
            throw error
          }
        })
    }
  },
  /**
   * Calculates which rows should be visible for the user based on the provided
   * scroll top and window height. Because we know what the padding above and below
   * the middle row should be and which rows we have in the buffer we can calculate
   * what the start and end index for the visible rows in the buffer should be.
   */
  visibleByScrollTop(
    { getters, commit },
    { scrollTop = null, windowHeight = null }
  ) {
    if (scrollTop !== null && windowHeight !== null) {
      commit('SET_SCROLL_TOP', { scrollTop, windowHeight })
    } else {
      scrollTop = getters.getScrollTop
      windowHeight = getters.getWindowHeight
    }

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
  fetchByScrollTopDelayed(
    { dispatch },
    { gridId, scrollTop, windowHeight, fields, primary }
  ) {
    const fire = (scrollTop, windowHeight) => {
      lastFire = new Date().getTime()
      if (scrollTop === lastScrollTop) {
        return
      }
      lastScrollTop = scrollTop
      dispatch('fetchByScrollTop', {
        gridId,
        scrollTop,
        windowHeight,
        fields,
        primary,
      })
      dispatch('visibleByScrollTop', { scrollTop, windowHeight })
    }

    const difference = new Date().getTime() - lastFire
    if (difference > 100) {
      clearTimeout(fireTimeout)
      fire(scrollTop, windowHeight)
    } else {
      clearTimeout(fireTimeout)
      fireTimeout = setTimeout(() => {
        fire(scrollTop, windowHeight)
      }, 100)
    }
  },
  /**
   * Fetches an initial set of rows and adds that data to the store.
   */
  async fetchInitial(
    { dispatch, commit, getters },
    { gridId, fields, primary }
  ) {
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
    })
    data.results.forEach((part, index) => {
      populateRow(data.results[index])
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
    dispatch('updateSearch', { fields, primary })
  },
  /**
   * Refreshes the current state with fresh data. It keeps the scroll offset the same
   * if possible. This can be used when a new filter or sort is created. Will also
   * update search highlighting if a new activeSearchTerm and hideRowsNotMatchingSearch
   * are provided in the refreshEvent.
   */
  refresh({ dispatch, commit, getters }, { gridId, fields, primary }) {
    if (lastRefreshRequest !== null) {
      lastRefreshRequestSource.cancel('Cancelled in favor of new request')
    }
    lastRefreshRequestSource = axios.CancelToken.source()
    lastRefreshRequest = GridService(this.$client)
      .fetchCount({
        gridId,
        search: getters.getServerSearchTerm,
        cancelToken: lastRefreshRequestSource.token,
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
            cancelToken: lastRefreshRequestSource.token,
            search: getters.getServerSearchTerm,
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
          populateRow(data.results[index])
        })
        commit('ADD_ROWS', {
          rows: data.results,
          prependToRows: -getters.getBufferLimit,
          appendToRows: data.results.length,
          count: data.count,
          bufferStartIndex: offset,
          bufferLimit: data.results.length,
        })
        dispatch('updateSearch', { fields, primary })
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
   * Triggered when a row has been changed, or has a pending change in the provided
   * overrides.
   */
  onRowChange({ dispatch }, { view, row, fields, primary, overrides = {} }) {
    dispatch('updateMatchFilters', { view, row, fields, primary, overrides })
    dispatch('updateMatchSortings', { view, row, fields, primary, overrides })
    dispatch('updateSearchMatchesForRow', { row, fields, primary, overrides })
  },
  /**
   * Checks if the given row still matches the given view filters. The row's
   * matchFilters value is updated accordingly. It is also possible to provide some
   * override values that not actually belong to the row to do some preliminary checks.
   */
  updateMatchFilters(
    { commit },
    { view, row, fields, primary, overrides = {} }
  ) {
    const values = JSON.parse(JSON.stringify(row))
    Object.keys(overrides).forEach((key) => {
      values[key] = overrides[key]
    })
    // The value is always valid if the filters are disabled.
    const matches = view.filters_disabled
      ? true
      : matchSearchFilters(
          this.$registry,
          view.filter_type,
          view.filters,
          primary === null ? fields : [primary, ...fields],
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
      primary = null,
      activeSearchTerm = state.activeSearchTerm,
      hideRowsNotMatchingSearch = state.hideRowsNotMatchingSearch,
      refreshMatchesOnClient = true,
    }
  ) {
    commit('SET_SEARCH', { activeSearchTerm, hideRowsNotMatchingSearch })
    if (refreshMatchesOnClient) {
      getters.getAllRows.forEach((row) =>
        dispatch('updateSearchMatchesForRow', { row, fields, primary })
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
    { row, fields, primary = null, overrides }
  ) {
    if (fields === undefined || primary === null) {
      throw new Error('FIELDS OR PRIMARY CANT BE NULL @TODO')
    }

    const rowSearchMatches = calculateSingleRowSearchMatches(
      row,
      getters.getActiveSearchTerm,
      getters.isHidingRowsNotMatchingSearch,
      [primary, ...fields],
      this.$registry,
      overrides
    )

    commit('SET_ROW_SEARCH_MATCHES', rowSearchMatches)
  },
  /**
   * Checks if the given row index is still the same. The row's matchSortings value is
   * updated accordingly. It is also possible to provide some override values that not
   * actually belong to the row to do some preliminary checks.
   */
  updateMatchSortings(
    { commit, getters },
    { view, row, fields, primary = null, overrides = {} }
  ) {
    const values = JSON.parse(JSON.stringify(row))
    Object.keys(overrides).forEach((key) => {
      values[key] = overrides[key]
    })

    const allRows = getters.getAllRows
    const currentIndex = getters.getAllRows.findIndex((r) => r.id === row.id)
    const sortedRows = JSON.parse(JSON.stringify(allRows))
    sortedRows[currentIndex] = values
    sortedRows.sort(
      getRowSortFunction(this.$registry, view.sortings, fields, primary)
    )
    const newIndex = sortedRows.findIndex((r) => r.id === row.id)

    commit('SET_ROW_MATCH_SORTINGS', { row, value: currentIndex === newIndex })
  },
  /**
   * Updates a grid view field value. It will immediately be updated in the store
   * and only if the change request fails it will reverted to give a faster
   * experience for the user.
   */
  async updateValue(
    { commit, dispatch },
    { table, view, row, field, fields, primary, value, oldValue }
  ) {
    commit('SET_VALUE', { row, field, value })
    dispatch('onRowChange', { view, row, fields, primary })

    const fieldType = this.$registry.get('field', field._.type.type)
    const newValue = fieldType.prepareValueForUpdate(field, value)
    const values = {}
    values[`field_${field.id}`] = newValue

    try {
      await RowService(this.$client).update(table.id, row.id, values)
    } catch (error) {
      commit('SET_VALUE', { row, field, value: oldValue })
      dispatch('onRowChange', { view, row, fields, primary })
      throw error
    }
  },
  /**
   * Creates a new row. Based on the default values of the fields a row is created
   * which will be added to the store. Only if the request fails the row is removed.
   */
  async create(
    { commit, getters, dispatch },
    { view, table, fields, primary, values = {}, before = null }
  ) {
    // Fill the not provided values with the empty value of the field type so we can
    // immediately commit the created row to the state.
    const allFields = [primary].concat(fields)
    allFields.forEach((field) => {
      const name = `field_${field.id}`
      if (!(name in values)) {
        const fieldType = this.$registry.get('field', field._.type.type)
        const empty = fieldType.getEmptyValue(field)
        values[name] = empty
      }
    })

    // Populate the row and set the loading state to indicate that the row has not
    // yet been added.
    const row = _.assign({}, values)
    populateRow(row)
    row.id = uuid()
    row._.loading = true

    if (before !== null) {
      // If the row has been placed before another row we can specifically insert to
      // the row at a calculated index.
      const index = getters.getAllRows.findIndex((r) => r.id === before.id)
      const change = new BigNumber('0.00000000000000000001')
      row.order = new BigNumber(before.order).minus(change).toString()
      commit('INSERT_ROW_AT', { row, index })
    } else {
      // By default the row is inserted at the end.
      commit('ADD_ROWS', {
        rows: [row],
        prependToRows: 0,
        appendToRows: 1,
        count: getters.getCount + 1,
        bufferStartIndex: getters.getBufferStartIndex,
        bufferLimit: getters.getBufferLimit + 1,
      })
    }

    // Recalculate all the values.
    dispatch('visibleByScrollTop', {
      scrollTop: null,
      windowHeight: null,
    })

    dispatch('onRowChange', { view, row, fields, primary })

    try {
      const { data } = await RowService(this.$client).create(
        table.id,
        values,
        before !== null ? before.id : null
      )
      commit('FINALIZE_ROW', { oldId: row.id, id: data.id, order: data.order })
    } catch (error) {
      commit('DELETE_ROW', row.id)
      throw error
    }
  },
  /**
   * Forcefully create a new row without making a call to the backend. It also
   * checks if the row matches the filters and sortings and if not it will be
   * removed from the buffer.
   */
  forceCreate(
    { commit, dispatch, getters },
    { view, fields, primary, values, getScrollTop }
  ) {
    const row = _.assign({}, values)
    populateRow(row)
    commit('ADD_ROWS', {
      rows: [row],
      prependToRows: 0,
      appendToRows: 1,
      count: getters.getCount + 1,
      bufferStartIndex: getters.getBufferStartIndex,
      bufferLimit: getters.getBufferLimit + 1,
    })
    dispatch('visibleByScrollTop', {
      scrollTop: null,
      windowHeight: null,
    })
    dispatch('onRowChange', { view, row, fields, primary })
    dispatch('refreshRow', { grid: view, row, fields, primary, getScrollTop })
  },
  /**
   * Forcefully update an existing row without making a call to the backend. It
   * could be that the row does not exist in the buffer, but actually belongs in
   * there. So after creating or updating the row we can check if it belongs
   * there and if not it will be deleted.
   */
  forceUpdate(
    { dispatch, commit, getters },
    { view, fields, primary, values, getScrollTop }
  ) {
    const row = getters.getRow(values.id)
    if (row === undefined) {
      return dispatch('forceCreate', {
        view,
        fields,
        primary,
        values,
        getScrollTop,
      })
    } else {
      commit('UPDATE_ROW', { row, values })
    }

    dispatch('onRowChange', { view, row, fields, primary })
    dispatch('refreshRow', { grid: view, row, fields, primary, getScrollTop })
  },
  /**
   * Deletes an existing row of the provided table. After deleting, the visible rows
   * range and the buffer are recalculated because we might need to show different
   * rows or add some rows to the buffer.
   */
  async delete(
    { commit, dispatch, getters },
    { table, grid, row, fields, primary, getScrollTop }
  ) {
    commit('SET_ROW_LOADING', { row, value: true })

    try {
      await RowService(this.$client).delete(table.id, row.id)
      dispatch('forceDelete', { grid, row, fields, primary, getScrollTop })
    } catch (error) {
      commit('SET_ROW_LOADING', { row, value: false })
      throw error
    }
  },
  /**
   * Deletes a row from the store without making a request to the backend. Note that
   * this should only be used if the row really isn't visible in the view anymore.
   * Otherwise wrong data could be fetched later. This action can also be used when a
   * row has been moved outside the current buffer.
   */
  forceDelete(
    { commit, dispatch, getters },
    { grid, row, fields, primary, getScrollTop, moved = false }
  ) {
    if (moved === 'up') {
      commit('DELETE_ROW_MOVED_UP', row.id)
    } else if (moved === 'down') {
      commit('DELETE_ROW_MOVED_DOWN', row.id)
    } else {
      commit('DELETE_ROW', row.id)
    }

    // We use the provided function to recalculate the scrollTop offset in order
    // to get fresh data.
    const scrollTop = getScrollTop()
    const windowHeight = getters.getWindowHeight

    dispatch('fetchByScrollTop', {
      gridId: grid.id,
      scrollTop,
      windowHeight,
      fields,
      primary,
    })
    dispatch('visibleByScrollTop', { scrollTop, windowHeight })
  },
  /**
   * Adds a field with a provided value to the rows in memory.
   */
  addField({ commit }, { field, value = null }) {
    commit('ADD_FIELD', { field, value })
  },
  /**
   * Updates the field options of a given field and also makes an API request to the
   * backend with the changed values. If the request fails the action is reverted.
   */
  async updateFieldOptionsOfField(
    { commit },
    { gridId, field, values, oldValues }
  ) {
    commit('UPDATE_FIELD_OPTIONS_OF_FIELD', {
      fieldId: field.id,
      values,
    })
    const updateValues = { field_options: {} }
    updateValues.field_options[field.id] = values

    try {
      await GridService(this.$client).update({ gridId, values: updateValues })
    } catch (error) {
      commit('UPDATE_FIELD_OPTIONS_OF_FIELD', {
        fieldId: field.id,
        values: oldValues,
      })
      throw error
    }
  },
  /**
   * Updates the field options of a given field in the store. So no API request to
   * the backend is made.
   */
  setFieldOptionsOfField({ commit }, { field, values }) {
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
    { dispatch },
    { gridId, newFieldOptions, oldFieldOptions }
  ) {
    dispatch('forceUpdateAllFieldOptions', newFieldOptions)
    const updateValues = { field_options: newFieldOptions }

    try {
      await GridService(this.$client).update({ gridId, values: updateValues })
    } catch (error) {
      dispatch('forceUpdateAllFieldOptions', oldFieldOptions)
      throw error
    }
  },
  /**
   * Forcefully updates all field options without making a call to the backend.
   */
  forceUpdateAllFieldOptions({ commit }, fieldOptions) {
    commit('UPDATE_ALL_FIELD_OPTIONS', fieldOptions)
  },
  /**
   * Updates the order of all the available field options. The provided order parameter
   * should be an array containing the field ids in the correct order.
   */
  async updateFieldOptionsOrder(
    { commit, getters, dispatch },
    { gridId, order }
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
      gridId,
      oldFieldOptions,
      newFieldOptions,
    })
  },
  /**
   * Deletes the field options of the provided field id if they exist.
   */
  forceDeleteFieldOptions({ commit }, fieldId) {
    commit('DELETE_FIELD_OPTIONS', fieldId)
  },
  setRowHover({ commit }, { row, value }) {
    commit('SET_ROW_HOVER', { row, value })
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
    { grid, row, field, fields, primary, getScrollTop }
  ) {
    commit('REMOVE_ROW_SELECTED_BY', { row, fieldId: field.id })
    dispatch('refreshRow', { grid, row, fields, primary, getScrollTop })
  },
  /**
   * The row is going to be removed or repositioned if the matchFilters and
   * matchSortings state is false. It will make the state correct.
   */
  refreshRow(
    { dispatch, commit, getters },
    { grid, row, fields, primary, getScrollTop }
  ) {
    const rowShouldBeHidden = !row._.matchFilters || !row._.matchSearch
    if (row._.selectedBy.length === 0 && rowShouldBeHidden) {
      dispatch('forceDelete', { grid, row, fields, primary, getScrollTop })
      return
    }

    if (row._.selectedBy.length === 0 && !row._.matchSortings) {
      const sortFunction = getRowSortFunction(
        this.$registry,
        grid.sortings,
        fields,
        primary
      )
      commit('SORT_ROWS', sortFunction)

      // We cannot know for sure if the row has been moved outside the scope of the
      // current buffer. Therefore if the row is at the beginning or the end of the
      // buffer we are going to remove it. This doesn't matter because the
      // fetchByScrollTop action, which is called in the forceDelete action, will fix
      // the buffer automatically.
      const up = getters.isFirst(row.id) && getters.getBufferStartIndex > 0
      const down =
        getters.isLast(row.id) && getters.getBufferEndIndex < getters.getCount
      if (up || down) {
        const moved = up ? 'up' : 'down'
        dispatch('forceDelete', {
          grid,
          row,
          fields,
          primary,
          getScrollTop,
          moved,
        })
      }
    }
  },
  setAddRowHover({ commit }, value) {
    commit('SET_ADD_ROW_HOVER', value)
  },
  setSelectedCell({ commit }, { rowId, fieldId }) {
    commit('SET_SELECTED_CELL', { rowId, fieldId })
  },
}

export const getters = {
  isLoading(state) {
    return state.loading
  },
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
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
