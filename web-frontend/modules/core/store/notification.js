import { uuid } from '@baserow/modules/core/utils/string'

export const state = () => ({
  connecting: false,
  failedConnecting: false,
  items: [],
})

export const mutations = {
  ADD(state, notification) {
    state.items.unshift(notification)
  },
  REMOVE(state, notification) {
    const index = state.items.indexOf(notification)
    state.items.splice(index, 1)
  },
  SET_CONNECTING(state, value) {
    state.connecting = value
  },
  SET_FAILED_CONNECTING(state, value) {
    state.failedConnecting = value
  },
}

export const actions = {
  /**
   * Shows a notification message to the user.
   */
  add({ commit }, { type, title = null, message = null, data = null }) {
    commit('ADD', {
      id: uuid(),
      type,
      title,
      message,
      data,
    })
  },
  info({ dispatch }, { title, message }) {
    dispatch('add', { type: 'info', title, message })
  },
  error({ dispatch }, { title, message }) {
    dispatch('add', { type: 'error', title, message })
  },
  warning({ dispatch }, { title, message }) {
    dispatch('add', { type: 'warning', title, message })
  },
  success({ dispatch }, { title, message }) {
    dispatch('add', { type: 'success', title, message })
  },
  restore({ dispatch }, restoreData) {
    dispatch('add', {
      type: 'restore',
      data: restoreData,
    })
  },
  remove({ commit }, notification) {
    commit('REMOVE', notification)
  },
  setConnecting({ commit }, value) {
    if (value) {
      commit('SET_FAILED_CONNECTING', false)
    }
    commit('SET_CONNECTING', value)
  },
  setFailedConnecting({ commit }, value) {
    if (value) {
      commit('SET_CONNECTING', false)
    }
    commit('SET_FAILED_CONNECTING', value)
  },
}

export const getters = {}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
