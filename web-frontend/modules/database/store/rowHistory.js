import RowHistoryService from '@baserow/modules/database/services/rowHistory'

export const state = () => ({
  entries: [],
  loading: false,
  loaded: false,
  totalCount: 0,
  loadedRowId: false,
  loadedTableId: false,
})

export const mutations = {
  ADD_ENTRIES(state, { entries }) {
    state.entries = entries
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
}

export const actions = {
  async fetchInitial({ commit }, { tableId, rowId }) {
    commit('RESET_ENTRIES')
    commit('SET_LOADING', true)
    commit('SET_LOADED', false)
    try {
      const { data } = await RowHistoryService(this.$client).fetchAll(
        tableId,
        rowId
      )
      commit('ADD_ENTRIES', { entries: data.results })
      commit('SET_TOTAL_COUNT', data.count)
      commit('SET_LOADED_TABLE_AND_ROW', { tableId, rowId })
      commit('SET_LOADED', true)
    } finally {
      commit('SET_LOADING', false)
    }
  },
}

export const getters = {
  getSortedEntries(state) {
    return state.entries
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
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
