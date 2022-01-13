import Vue from 'vue'
import axios from 'axios'
import { RefreshCancelledError } from '@baserow/modules/core/errors'
import { clone } from '@baserow/modules/core/utils/object'
import {
  getRowSortFunction,
  matchSearchFilters,
} from '@baserow/modules/database/utils/view'
import RowService from '@baserow/modules/database/services/row'

/**
 * This view store mixin can be used to efficiently keep and maintain the rows of a
 * table/view without fetching all the rows at once. It first fetches an initial set
 * of rows and creates an array in the state containing these rows and adds a `null`
 * object for every un-fetched row.
 *
 * It can correctly handle when new rows are created, updated or deleted without
 * needing every row in the state. Components that make use of this store mixin
 * just have to dispatch an action telling which rows are currently visible and the
 * store handles the rest. Rows that are un-fetched, so when they are `null`, must
 * be shown in a loading state if the user is looking at them.
 *
 * Example of how the state of rows could look:
 *
 * ```
 * rows = [
 *   { id: 1, order: '1.00000000000000000000', field_1: 'Name' },
 *   { id: 2, order: '2.00000000000000000000', field_1: 'Name' },
 *   { id: 3, order: '3.00000000000000000000', field_1: 'Name' },
 *   { id: 4, order: '4.00000000000000000000', field_1: 'Name' },
 *   null,
 *   null,
 *   null,
 *   null,
 *   { id: 9, order: '10.00000000000000000000', field_1: 'Name' },
 *   { id: 10, order: '10.00000000000000000000', field_1: 'Name' },
 *   null,
 *   null
 * ]
 * ```
 */
export default ({ service, populateRow }) => {
  let lastRequestSource = null

  /**
   * This helper function calculates the most optimal `limit` `offset` range of rows
   * that must be fetched. Based on the provided visible `startIndex` and `endIndex`
   * we know which rows must be fetched because those values are `null` in the
   * provided `rows` array. If a request must be made, we want to do so in the most
   * efficient manner, so we want to respect the ideal request size by filling up
   * the request with other rows before and after the range that must also be fetched.
   * This function checks if there are other `null` rows close to the range and if
   * so, it tries to include them in the range.
   *
   * @param rows        An array containing the rows that we have fetched already.
   * @param requestSize The ideal request when making a request to the server.
   * @param startIndex  The start index of the visible rows.
   * @param endIndex    The end index of the visible rows.
   */
  const getRangeToFetch = (rows, requestSize, startIndex, endIndex) => {
    const visibleRows = rows.slice(startIndex, endIndex + 1)

    const firstNullIndex = visibleRows.findIndex((row) => row === null)
    const lastNullIndex = visibleRows.lastIndexOf(null)

    // If all of the visible rows have been fetched, so none of them are `null`, we
    // don't have to do anything.
    if (firstNullIndex === -1) {
      return
    }

    // Figure out what the request size is. In almost all cases this is going to
    // be the configured request size, but it could be that more rows must be visible
    // and in that case we want to increase it
    const maxRequestSize = Math.max(startIndex - endIndex, requestSize)

    // The initial offset can be the first `null` found in the range.
    let offset = startIndex + firstNullIndex
    let limit = lastNullIndex - firstNullIndex + 1

    // Because we have an ideal request size and this is often higher than the
    // visible rows, we want to efficiently fetch additional rows that are close
    // to the visible range.
    while (limit < maxRequestSize) {
      const previous = rows[offset - 1]
      const next = rows[offset + limit + 1]

      // If both the previous and next item are not `null`, which means there is
      // no un-fetched row before or after the range anymore, we want to stop the for
      // loop because there is nothing to fetch.
      if (previous !== null && next !== null) {
        break
      }
      if (previous === null) {
        offset -= 1
        limit += 1
      }
      if (next === null) {
        limit += 1
      }
    }

    // The `limit` could exceed the `maxRequestSize` if it's an odd number because it
    // checks if there is an un-fetched row before and after in one loop.
    return { offset, limit: Math.min(limit, maxRequestSize) }
  }

  const state = () => ({
    // If another visible rows action has been dispatched whilst a previous action
    // is still fetching rows, the new action is temporarily delayed and its
    // parameters are stored here.
    delayedRequest: null,
    // Holds the last requested start and end index of the currently visible rows
    visibleRange: {
      startIndex: 0,
      endIndex: 0,
    },
    // The ideal number of rows to fetch when making a request.
    requestSize: 100,
    // The current view id.
    viewId: -1,
    // Indicates whether the store is currently fetching another batch of rows.
    fetching: false,
    // A list of all the rows in the table. The ones that haven't been fetched yet
    // are `null`.
    rows: [],
    // The row that's in dragging state and is being moved to another position.
    draggingRow: null,
    // The row that the dragging row was before when the dragging state was started.
    // This is needed to revert the position if anything goes wrong or the escape
    // key was pressed.
    draggingOriginalBefore: null,
  })

  const mutations = {
    SET_DELAYED_REQUEST(state, delayedRequestParameters) {
      state.delayedRequest = delayedRequestParameters
    },
    SET_VISIBLE(state, { startIndex, endIndex }) {
      state.visibleRange.startIndex = startIndex
      state.visibleRange.endIndex = endIndex
    },
    SET_VIEW_ID(state, viewId) {
      state.viewId = viewId
    },
    SET_ROWS(state, rows) {
      Vue.set(state, 'rows', rows)
    },
    SET_FETCHING(state, value) {
      state.fetching = value
    },
    UPDATE_ROWS(state, { offset, rows }) {
      for (let i = 0; i < rows.length; i++) {
        const rowStoreIndex = i + offset
        const rowInStore = state.rows[rowStoreIndex]
        const row = rows[i]

        if (rowInStore === undefined || rowInStore === null) {
          // If the row doesn't yet exist in the store, we can populate the provided
          // row and set it.
          state.rows.splice(rowStoreIndex, 1, populateRow(row))
        } else {
          // If the row does exist in the store, we can extend it with the provided
          // data of the provided row so the state won't be lost.
          Object.assign(state.rows[rowStoreIndex], row)
        }
      }
    },
    INSERT_ROW_AT_INDEX(state, { index, row }) {
      state.rows.splice(index, 0, row)
    },
    DELETE_ROW_AT_INDEX(state, { index }) {
      state.rows.splice(index, 1)
    },
    MOVE_ROW(state, { oldIndex, newIndex }) {
      state.rows.splice(newIndex, 0, state.rows.splice(oldIndex, 1)[0])
    },
    UPDATE_ROW(state, { row, values }) {
      const index = state.rows.findIndex(
        (item) => item !== null && item.id === row.id
      )
      if (index !== -1) {
        Object.assign(state.rows[index], values)
      }
    },
    UPDATE_ROW_AT_INDEX(state, { index, values }) {
      Object.assign(state.rows[index], values)
    },
    ADD_FIELD_TO_ALL_ROWS(state, { field, value }) {
      const name = `field_${field.id}`
      state.rows.forEach((row) => {
        if (row !== null && !Object.prototype.hasOwnProperty.call(row, name)) {
          // We have to use the Vue.set function here to make it reactive immediately.
          // If we don't do this the value in the field components of the view and modal
          // don't have the correct value and will act strange.
          Vue.set(row, name, value)
        }
      })
    },
    START_ROW_DRAG(state, { index }) {
      state.rows[index]._.dragging = true
      state.draggingRow = state.rows[index]
      state.draggingOriginalBefore = state.rows[index + 1] || null
    },
    STOP_ROW_DRAG(state, { index }) {
      state.rows[index]._.dragging = false
      state.draggingRow = null
      state.draggingOriginalBefore = null
    },
  }

  const actions = {
    /**
     * This action fetches the initial set of rows via the provided service. After
     * that it will fill the state with the newly fetched rows and the rest will be
     * un-fetched `null` objects.
     */
    async fetchInitialRows(
      context,
      { viewId, fields, primary, initialRowArguments = {} }
    ) {
      const { commit, getters } = context
      commit('SET_VIEW_ID', viewId)
      const { data } = await service(this.$client).fetchRows({
        viewId,
        offset: 0,
        limit: getters.getRequestSize,
        ...initialRowArguments,
      })
      const rows = Array(data.count).fill(null)
      data.results.forEach((row, index) => {
        rows[index] = populateRow(row)
      })
      commit('SET_ROWS', rows)
      return data
    },
    /**
     * Should be called when the different rows are displayed to the user. This
     * could for example happen when a user scrolls. It will figure out which rows
     * have not been fetched and will make a request with the backend to replace to
     * missing ones if needed.
     */
    async fetchMissingRowsInNewRange(
      { dispatch, getters, commit },
      parameters
    ) {
      const { startIndex, endIndex } = parameters

      // If the store is already fetching a set of pages, we're temporarily storing
      // the parameters so that this action can be dispatched again with the latest
      // parameters.
      if (getters.getFetching) {
        commit('SET_DELAYED_REQUEST', parameters)
        return
      }

      // Check if the currently visible range isn't to same as the provided one
      // because we don't want to do anything in that case.
      const currentVisible = getters.getVisibleRange
      if (
        currentVisible.startIndex === startIndex &&
        currentVisible.endIndex === endIndex
      ) {
        return
      }

      // Update the last visible range to make sure this action isn't dispatched
      // multiple times.
      commit('SET_VISIBLE', { startIndex, endIndex })

      // Check what the ideal range is to fetch with the backend.
      const rangeToFetch = getRangeToFetch(
        getters.getRows,
        getters.getRequestSize,
        startIndex,
        endIndex
      )

      // If there is no ideal range or if the limit is 0, then there aren't any rows
      // to fetch so we can stop.
      if (rangeToFetch === undefined || rangeToFetch.limit === 0) {
        return
      }

      // We can only make one request at the same time, so we're going to to set the
      // fetching state to `true` to prevent multiple requests being fired
      // simultaneously.
      commit('SET_FETCHING', true)
      lastRequestSource = axios.CancelToken.source()
      try {
        const { data } = await service(this.$client).fetchRows({
          viewId: getters.getViewId,
          offset: rangeToFetch.offset,
          limit: rangeToFetch.limit,
          cancelToken: lastRequestSource.token,
        })
        commit('UPDATE_ROWS', {
          offset: rangeToFetch.offset,
          rows: data.results,
        })
      } catch (error) {
        if (axios.isCancel(error)) {
          throw new RefreshCancelledError()
        } else {
          lastRequestSource = null
          throw error
        }
      } finally {
        // Check if another `fetchMissingRowsInNewRange` action has been dispatched
        // while we were fetching the rows. If so, we need to dispatch the same
        // action again with the latest parameters.
        commit('SET_FETCHING', false)
        const delayedRequestParameters = getters.getDelayedRequest
        if (delayedRequestParameters !== null) {
          commit('SET_DELAYED_REQUEST', null)
          await dispatch('fetchMissingRowsInNewRange', delayedRequestParameters)
        }
      }
    },
    /**
     * Refreshes the row buffer by clearing all of the rows in the store and
     * re-fetching the currently visible rows. This is typically done when a filter has
     * changed and we can't trust what's in the store anymore.
     */
    async refresh(
      { dispatch, commit, getters },
      { fields, primary, includeFieldOptions = false }
    ) {
      // If another refresh or fetch request is currently running, we need to cancel
      // it because the response is most likely going to be outdated and we don't
      // need it anymore.
      if (lastRequestSource !== null) {
        lastRequestSource.cancel('Cancelled in favor of new request')
      }

      lastRequestSource = axios.CancelToken.source()

      try {
        // We first need to fetch the count of all rows because we need to know how
        // many rows there are in total to estimate what are new visible range it
        // going to be.
        commit('SET_FETCHING', true)
        const {
          data: { count },
        } = await service(this.$client).fetchCount({
          viewId: getters.getViewId,
          cancelToken: lastRequestSource.token,
        })

        // Create a new empty array containing un-fetched rows.
        const rows = Array(count).fill(null)
        let startIndex = 0
        let endIndex = 0

        if (count > 0) {
          // Figure out which range was previous visible and see if that still fits
          // within the new set of rows. Otherwise we're going to fall
          const currentVisible = getters.getVisibleRange
          startIndex = currentVisible.startIndex
          endIndex = currentVisible.endIndex
          const difference = count - endIndex

          if (difference < 0) {
            startIndex += difference
            endIndex += difference
          }

          // Based on the newly calculated range we can figure out which rows we want
          // to fetch from the backend to populate our store with. These should be the
          // rows that the user is going to look at.
          const rangeToFetch = getRangeToFetch(
            rows,
            getters.getRequestSize,
            startIndex,
            endIndex
          )

          // Only fetch visible rows if there are any.
          const {
            data: { results },
          } = await service(this.$client).fetchRows({
            viewId: getters.getViewId,
            offset: rangeToFetch.offset,
            limit: rangeToFetch.limit,
            includeFieldOptions,
            cancelToken: lastRequestSource.token,
          })

          results.forEach((row, index) => {
            rows[rangeToFetch.offset + index] = populateRow(row)
          })
        }

        commit('SET_ROWS', rows)
        commit('SET_VISIBLE', { startIndex, endIndex })
      } catch (error) {
        if (axios.isCancel(error)) {
          throw new RefreshCancelledError()
        } else {
          lastRequestSource = null
          throw error
        }
      } finally {
        commit('SET_FETCHING', false)
      }
    },
    /**
     * Adds a field with a provided value to the rows in the store. This will for
     * example be called when a new field has been created.
     */
    addField({ commit }, { field, value = null }) {
      commit('ADD_FIELD_TO_ALL_ROWS', { field, value })
    },
    /**
     * Check if the provided row matches the provided view filters.
     */
    rowMatchesFilters(context, { view, fields, primary, row, overrides = {} }) {
      const values = JSON.parse(JSON.stringify(row))
      Object.assign(values, overrides)

      // The value is always valid if the filters are disabled.
      return view.filters_disabled
        ? true
        : matchSearchFilters(
            this.$registry,
            view.filter_type,
            view.filters,
            primary === null ? fields : [primary, ...fields],
            values
          )
    },
    /**
     * Returns the index that the provided row was supposed to have if it was in the
     * store. Because some rows haven't been fetched from the backend, we need to
     * figure out which `null` object could have been the row in the store.
     */
    findIndexOfNotExistingRow({ getters }, { view, fields, primary, row }) {
      const sortFunction = getRowSortFunction(
        this.$registry,
        view.sortings,
        fields,
        primary
      )
      const allRows = getters.getRows
      let index = allRows.findIndex((existingRow) => {
        return existingRow !== null && sortFunction(row, existingRow) < 0
      })
      let isCertain = true

      if (index === -1 && allRows[allRows.length - 1] !== null) {
        // If we don't know where to position the new row and the last row is null, we
        // can safely assume it's the last row because when finding the index we
        // only check if the new row is before an existing row.
        index = allRows.length
      } else if (index === -1) {
        // If we don't know where to position the new row we can assume near the
        // end, but we're not sure where exactly. Because of that we'll add it as
        // null to the end.
        index = allRows.length
        isCertain = false
      } else if (allRows[index - 1] === null) {
        // If the row must inserted at the beginning of a known chunk of fetched
        // rows, we can't know for sure it actually has to be inserted directly before.
        // In that case, we will insert it as null.
        isCertain = false
      }

      return { index, isCertain }
    },
    /**
     * Returns the index of a row that's in the store. This also works if the row
     * hasn't been fetched yet, it will then point to the `null` object representing
     * the row.
     */
    findIndexOfExistingRow(
      { dispatch, getters },
      { view, fields, primary, row }
    ) {
      const sortFunction = getRowSortFunction(
        this.$registry,
        view.sortings,
        fields,
        primary
      )
      const allRows = getters.getRows
      let index = allRows.findIndex((existingRow) => {
        return existingRow !== null && existingRow.id === row.id
      })
      let isCertain = true

      if (index === -1) {
        // If the row is not found in the index, we will have to figure out what the
        // position could be.
        index = allRows.findIndex((existingRow) => {
          return existingRow !== null && sortFunction(row, existingRow) < 0
        })
        isCertain = false

        if (index === -1 && allRows[allRows.length - 1] === null) {
          // If we don't know where to position the existing row and the last row is
          // null, we can safely assume it's the last row because when finding the
          // index we only check if the new row is before an existing row.
          index = allRows.length
        }

        if (index >= 0) {
          index -= 1
        }
      }

      return { index, isCertain }
    },
    /**
     * Creates a new row and adds it to the store if needed.
     */
    async createNewRow(
      { dispatch, commit, getters },
      { view, table, fields, primary, values }
    ) {
      // First prepare an object that we can send to the backend.
      const allFields = [primary].concat(fields)
      const preparedValues = {}
      allFields.forEach((field) => {
        const name = `field_${field.id}`
        const fieldType = this.$registry.get('field', field._.type.type)

        if (fieldType.isReadOnly) {
          return
        }

        preparedValues[name] = Object.prototype.hasOwnProperty.call(
          values,
          name
        )
          ? (preparedValues[name] = fieldType.prepareValueForUpdate(
              field,
              values[name]
            ))
          : fieldType.getEmptyValue(field)
      })

      const { data } = await RowService(this.$client).create(
        table.id,
        preparedValues
      )
      return await dispatch('afterNewRowCreated', {
        view,
        fields,
        primary,
        values: data,
      })
    },
    /**
     * When a new row is created and it doesn't yet in exist in this store, so we must
     * insert it in the right position. Based on the values of the row we can
     * calculate if the row should be added (matches filters) and at which position
     * (sortings).
     *
     * Because we only fetch the rows from the backend that are actually needed, it
     * could be that we can't figure out where the row should be inserted. In that
     * case, we add a `null` in the area that is unknown. The store
     * already has other null values for rows that are un-fetched. So the un-fetched
     * row representations that are `null` in the array will be fetched automatically
     * when the user wants to see them.
     */
    async afterNewRowCreated(
      { dispatch, getters, commit },
      { view, fields, primary, values }
    ) {
      let row = clone(values)
      populateRow(row)

      // Check if the row matches the filters. If not, we don't have to do anything
      // because we know this row does not exist in the view.
      if (
        !(await dispatch('rowMatchesFilters', { view, fields, primary, row }))
      ) {
        return
      }

      const { index, isCertain } = await dispatch('findIndexOfNotExistingRow', {
        view,
        fields,
        primary,
        row,
      })

      // If we're not completely certain about the target index of the new row, we
      // must add it as `null` to the store because then it will automatically be
      // fetched when the user looks at it.
      if (!isCertain) {
        row = null
      }

      commit('INSERT_ROW_AT_INDEX', { index, row })
    },
    /**
     * Updates the value of a row and make the updates to the store accordingly.
     */
    async updateRowValue(
      { commit, dispatch },
      { table, view, row, field, fields, primary, value, oldValue }
    ) {
      const fieldType = this.$registry.get('field', field._.type.type)
      const allFields = [primary].concat(fields)
      const newValues = {}
      const newValuesForUpdate = {}
      const oldValues = {}
      const fieldName = `field_${field.id}`
      newValues[fieldName] = value
      newValuesForUpdate[fieldName] = fieldType.prepareValueForUpdate(
        field,
        value
      )
      oldValues[fieldName] = oldValue

      allFields.forEach((fieldToCall) => {
        const fieldType = this.$registry.get('field', fieldToCall._.type.type)
        const fieldToCallName = `field_${fieldToCall.id}`
        const currentFieldValue = row[fieldToCallName]
        const optimisticFieldValue = fieldType.onRowChange(
          row,
          field,
          value,
          oldValue,
          fieldToCall,
          currentFieldValue
        )

        if (currentFieldValue !== optimisticFieldValue) {
          newValues[fieldToCallName] = optimisticFieldValue
          oldValues[fieldToCallName] = currentFieldValue
        }
      })

      await dispatch('afterExistingRowUpdated', {
        view,
        fields,
        primary,
        row,
        values: newValues,
      })

      try {
        const { data } = await RowService(this.$client).update(
          table.id,
          row.id,
          newValuesForUpdate
        )
        commit('UPDATE_ROW', { row, values: data })
      } catch (error) {
        dispatch('updatedExistingRow', {
          view,
          fields,
          primary,
          row,
          values: oldValues,
        })
        throw error
      }
    },
    /**
     * When an existing row is updated, the state in the store must also be updated.
     * Because we always receive the old and new state we can calculate if the row
     * already existed in store. If it does exist, but the row was not fetched yet,
     * so in a `null` state, we can still figure out what the index was supposed to
     * be and take action on that.
     *
     * It works very similar to what happens when a row is created. If we can be
     * sure about the new position then we can update the and keep it's data. If we
     * can't be 100% sure, the row will be updated as `null`.
     */
    async afterExistingRowUpdated(
      { dispatch, commit },
      { view, fields, primary, row, values }
    ) {
      const oldRow = clone(row)
      let newRow = Object.assign(clone(row), values)
      populateRow(oldRow)
      populateRow(newRow)

      const oldRowMatches = await dispatch('rowMatchesFilters', {
        view,
        fields,
        primary,
        row: oldRow,
      })
      const newRowMatches = await dispatch('rowMatchesFilters', {
        view,
        fields,
        primary,
        row: newRow,
      })

      if (oldRowMatches && !newRowMatches) {
        // If the old row did match the filters, but after the update it does not
        // anymore, we can safely remove it from the store.
        await dispatch('afterExistingRowDeleted', {
          view,
          fields,
          primary,
          row,
        })
      } else if (!oldRowMatches && newRowMatches) {
        // If the old row didn't match filters, but the updated one does, we need to
        // add it to the store.
        await dispatch('afterNewRowCreated', {
          view,
          fields,
          primary,
          values: newRow,
        })
      } else if (oldRowMatches && newRowMatches) {
        // If the old and updated row already exists in the store, we need to update is.
        const { index: oldIndex, isCertain: oldIsCertain } = await dispatch(
          'findIndexOfExistingRow',
          {
            view,
            fields,
            primary,
            row: oldRow,
          }
        )
        const findNewRow = await dispatch('findIndexOfNotExistingRow', {
          view,
          fields,
          primary,
          row: newRow,
        })
        let { index: newIndex } = findNewRow
        const { isCertain: newIsCertain } = findNewRow

        // When finding the new index, the old row still existed in the store. When
        // the newIndex is higher than the old index, we need to compensate for this
        // because when figuring out the new position, we expected the existing row
        // not to be there.
        if (newIndex > oldIndex) {
          newIndex -= 1
        }

        if (oldIsCertain && newIsCertain) {
          // If both the old and updated are certain, we can just update the values
          // of the row so the original row, including the state, will persist.
          commit('UPDATE_ROW_AT_INDEX', { index: oldIndex, values })

          if (oldIndex !== newIndex) {
            // If the index has changed we want to move the row. We're moving it and
            // not recreating it because we want the state to persist.
            commit('MOVE_ROW', { oldIndex, newIndex })
          }
        } else {
          // If either the old and updated row is not certain, which means it's in a
          // `null` state, there is no row to persist to we can easily recreate it
          // at the right position.
          if (!newIsCertain) {
            newRow = null
          }

          commit('DELETE_ROW_AT_INDEX', { index: oldIndex })
          commit('INSERT_ROW_AT_INDEX', { index: newIndex, row: newRow })
        }
      }
    },
    /**
     * When a new row deleted and it does exist in the store, it must be deleted
     * removed from is. Based on the provided values of the row we can figure out if
     * it was in the store and we can figure out what index it has.
     */
    async afterExistingRowDeleted(
      { dispatch, commit },
      { view, fields, primary, row }
    ) {
      row = clone(row)
      populateRow(row)

      // Check if the row matches the filters. If not, we don't have to do anything
      // because we know this row does not exist in the view.
      if (
        !(await dispatch('rowMatchesFilters', { view, fields, primary, row }))
      ) {
        return
      }

      const { index } = await dispatch('findIndexOfExistingRow', {
        view,
        fields,
        primary,
        row,
      })
      commit('DELETE_ROW_AT_INDEX', { index })
    },
    /**
     * Brings the provided row in a dragging state so that it can freely moved to
     * another position.
     */
    startRowDrag({ commit, getters }, { row }) {
      const rows = getters.getRows
      const index = rows.findIndex((r) => r !== null && r.id === row.id)
      commit('START_ROW_DRAG', { index })
    },
    /**
     * This action stops the dragging state of a row, will figure out which values
     * need to updated and will make a call to the backend. If something goes wrong,
     * the row is moved back to the position.
     */
    async stopRowDrag(
      { dispatch, commit, getters },
      { table, view, fields, primary }
    ) {
      const row = getters.getDraggingRow

      if (row === null) {
        return
      }

      const rows = getters.getRows
      const index = rows.findIndex((r) => r !== null && r.id === row.id)
      const before = rows[index + 1] || null
      const originalBefore = getters.getDraggingOriginalBefore

      commit('STOP_ROW_DRAG', { index })

      if (originalBefore !== before) {
        try {
          const { data } = await RowService(this.$client).move(
            table.id,
            row.id,
            before !== null ? before.id : null
          )
          commit('UPDATE_ROW', { row, values: data })
        } catch (error) {
          dispatch('cancelRowDrag', { view, fields, primary, row, stop: false })
          throw error
        }
      }
    },
    /**
     * Cancels the current row drag action by reverting back to the original position
     * while respecting any new rows that have been moved into there in the mean time.
     */
    cancelRowDrag(
      { dispatch, getters, commit },
      { view, fields, primary, row, stop = true }
    ) {
      if (stop) {
        const rows = getters.getRows
        const index = rows.findIndex((r) => r !== null && r.id === row.id)
        commit('STOP_ROW_DRAG', { index })
      }

      dispatch('afterExistingRowUpdated', {
        view,
        fields,
        primary,
        row,
        values: row,
      })
    },
    /**
     * Moves the provided existing row to the position of the target row.
     *
     * @param row           The row object that must be moved.
     * @param targetRow     Will be placed before or after the provided row.
     */
    forceMoveRowBefore({ getters, commit }, { row, targetRow }) {
      const rows = getters.getRows
      const newIndex = rows.findIndex(
        (r) => r !== null && r.id === targetRow.id
      )

      if (newIndex > -1) {
        const oldIndex = rows.findIndex((r) => r !== null && r.id === row.id)
        commit('MOVE_ROW', { oldIndex, newIndex })
        return true
      }

      return false
    },
  }

  const getters = {
    getViewId(state) {
      return state.viewId
    },
    getDelayedRequest(state) {
      return state.delayedRequest
    },
    getVisibleRange(state) {
      return state.visibleRange
    },
    getRequestSize(state) {
      return state.requestSize
    },
    getFetching(state) {
      return state.fetching
    },
    getRows(state) {
      return state.rows
    },
    getDraggingRow(state) {
      return state.draggingRow
    },
    getDraggingOriginalBefore(state) {
      return state.draggingOriginalBefore
    },
  }

  return {
    namespaced: true,
    state,
    getters,
    actions,
    mutations,
  }
}
