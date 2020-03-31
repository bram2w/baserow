import { uuid } from '@baserow/modules/core/utils/string'

export const state = () => ({
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
}

export const actions = {
  /**
   * Shows a notification message to the user.
   */
  add({ commit }, { type, title, message }) {
    commit('ADD', {
      id: uuid(),
      type,
      title,
      message,
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
  remove({ commit }, notification) {
    commit('REMOVE', notification)
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
