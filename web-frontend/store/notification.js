import { uuid } from '@/utils/string'

export const state = () => ({
  items: []
})

export const mutations = {
  ADD(state, notification) {
    state.items.unshift(notification)
  },
  REMOVE(state, notification) {
    const index = state.items.indexOf(notification)
    state.items.splice(index, 1)
  }
}

export const actions = {
  add({ commit }, { type, title, message }) {
    commit('ADD', {
      id: uuid(),
      type: type,
      title: title,
      message: message
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
  }
}

export const getters = {}
