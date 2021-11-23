import Vue from 'vue'

/**
 * This store exists to always keep a copy of the row that's being edited via the
 * row edit modal. It sometimes happen that row from the original source, where it was
 * reactive with doesn't exist anymore. To make sure the modal still works in that
 * case, we always store a copy here and if it doesn't exist in the original data
 * source it accepts real time updates.
 */
export const state = () => ({
  id: -1,
  exists: false,
  row: {},
})

export const mutations = {
  CLEAR(state) {
    state.id = -1
    state.exists = false
    state.row = {}
  },
  OPEN(state, { id, exists, row }) {
    state.id = id
    state.exists = exists
    state.row = row
  },
  SET_EXISTS(state, value) {
    state.exists = value
  },
  REPLACE_ROW(state, row) {
    Vue.set(state, 'row', row)
  },
  UPDATE_ROW(state, row) {
    Object.assign(state.row, row)
  },
}

export const actions = {
  clear({ commit }) {
    commit('CLEAR')
  },
  open({ commit }, { id, exists, row }) {
    commit('OPEN', { id, exists, row })
  },
  doesNotExist({ commit }) {
    commit('SET_EXISTS', false)
  },
  doesExist({ commit }, { row }) {
    commit('SET_EXISTS', true)
    commit('REPLACE_ROW', row)
  },
  updated({ commit, getters }, { values }) {
    if (values.id === getters.id && !getters.exists) {
      commit('UPDATE_ROW', values)
    }
  },
}

export const getters = {
  id: (state) => {
    return state.id
  },
  exists: (state) => {
    return state.exists
  },
  row: (state) => {
    return state.row
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
