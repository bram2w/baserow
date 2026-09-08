import _ from 'lodash'

import moment from '@baserow/modules/core/moment'

import RowHistoryService from '@baserow/modules/database/services/rowHistory'

export const state = () => ({
  entries: [],
  loading: false,
  loaded: false,
  totalCount: 0,
  loadedRowId: false,
  loadedTableId: false,
  requestId: 0,
  revision: 0,
})

export const mutations = {
  ADD_ENTRIES(state, { entries }) {
    entries.forEach((newEntry) => {
      const existingIndex = state.entries.findIndex((e) => e.id === newEntry.id)
      if (existingIndex >= 0) {
        // Prevent duplicates by just replacing them inline
        state.entries.splice(existingIndex, 1, newEntry)
      } else {
        state.entries.push(newEntry)
      }
    })
  },
  RESET_ENTRIES(state) {
    state.entries = []
    state.totalCount = 0
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_LOADED(state, loaded) {
    state.loaded = loaded
  },
  SET_LOADED_TABLE_AND_ROW(state, { tableId, rowId }) {
    state.loadedRowId = rowId
    state.loadedTableId = tableId
  },
  SET_TOTAL_COUNT(state, totalCount) {
    state.totalCount = totalCount
  },
  START_REQUEST(state) {
    state.requestId++
  },
  INVALIDATE(state) {
    state.loaded = false
    state.revision++
  },
}

export const actions = {
  async fetchInitial(
    { commit, state },
    { tableId, rowId, realtimeRecovery = false }
  ) {
    const { $client } = this
    commit('START_REQUEST')
    const requestId = state.requestId
    const revision = state.revision
    const preserveEntries =
      realtimeRecovery &&
      state.loadedTableId === tableId &&
      state.loadedRowId === rowId
    const previousIds = new Set(
      preserveEntries ? state.entries.map((entry) => entry.id) : []
    )
    // Establish the row before fetching so live entries arriving during the
    // request are retained. A later row/request owns the store if we are stale.
    commit('SET_LOADED_TABLE_AND_ROW', { tableId, rowId })
    if (!preserveEntries) {
      commit('RESET_ENTRIES')
    }
    commit('SET_LOADING', true)
    commit('SET_LOADED', false)
    try {
      const { data } = await RowHistoryService($client).fetchAll({
        tableId,
        rowId,
        limit: 30,
        realtimeRecovery,
      })
      if (requestId !== state.requestId) {
        return
      }
      const fetchedIds = new Set(data.results.map((entry) => entry.id))
      const newest = data.results[0]
      // The API page is ordered by action_timestamp DESC, id DESC. Delayed live
      // copies below its newest entry are already counted and belong to later
      // pages; merging those would move the pagination offset past unseen rows.
      const liveEntries = state.entries.filter((entry) => {
        // Cached entries stay visible on errors, but the successful snapshot
        // replaces them. Only events received during this request are merged.
        if (previousIds.has(entry.id)) {
          return false
        }
        if (!newest || fetchedIds.has(entry.id)) {
          return true
        }
        const timeDifference = moment
          .utc(entry.timestamp ?? 0)
          .diff(moment.utc(newest.timestamp ?? 0))
        return (
          timeDifference > 0 || (timeDifference === 0 && entry.id > newest.id)
        )
      })
      const addedCount = liveEntries.filter(
        (entry) => !fetchedIds.has(entry.id)
      ).length
      commit('RESET_ENTRIES')
      commit('ADD_ENTRIES', { entries: data.results })
      commit('ADD_ENTRIES', { entries: liveEntries })
      commit('SET_TOTAL_COUNT', data.count + addedCount)
      commit('SET_LOADED', revision === state.revision)
    } finally {
      if (requestId === state.requestId) {
        commit('SET_LOADING', false)
      }
    }
  },
  async fetchNextPage({ commit, getters, state }, { tableId, rowId }) {
    if (
      state.loading ||
      !state.loaded ||
      state.loadedTableId !== tableId ||
      state.loadedRowId !== rowId
    ) {
      return
    }
    const { $client } = this
    const requestId = state.requestId
    commit('SET_LOADING', true)
    try {
      const { data } = await RowHistoryService($client).fetchAll({
        tableId,
        rowId,
        offset: getters.getCurrentCount,
        limit: 30,
      })
      if (requestId !== state.requestId) {
        return
      }
      commit('ADD_ENTRIES', { entries: data.results })
      commit('SET_TOTAL_COUNT', Math.max(data.count, state.totalCount))
    } finally {
      if (requestId === state.requestId) {
        commit('SET_LOADING', false)
      }
    }
  },
  forceCreate({ commit, state }, { rowHistoryEntry, rowId, tableId }) {
    if (state.loadedTableId === tableId && state.loadedRowId === rowId) {
      const exists = state.entries.some(
        (entry) => entry.id === rowHistoryEntry.id
      )
      commit('ADD_ENTRIES', { entries: [rowHistoryEntry] })
      if (!exists) {
        commit('SET_TOTAL_COUNT', state.totalCount + 1)
      }
    }
  },
  invalidate({ commit }) {
    commit('INVALIDATE')
  },
}

export const getters = {
  getSortedEntries(state) {
    return _.sortBy(state.entries, (e) => -moment.utc(e.timestamp))
  },
  getCurrentCount(state) {
    return state.entries.length
  },
  getTotalCount(state) {
    return state.totalCount
  },
  getLoading(state) {
    return state.loading
  },
  getLoaded(state) {
    return state.loaded
  },
  getRevision(state) {
    return state.revision
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
