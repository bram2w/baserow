import Vue from 'vue'

const state = {}

const mutations = {
  SET_PARAMETER(state, { page, name, value }) {
    if (!page.parameters) {
      Vue.set(page, 'parameters', {})
    }
    page.parameters = { ...page.parameters, [name]: value }
  },
}

const actions = {
  setParameter({ commit }, { page, name, value }) {
    commit('SET_PARAMETER', { page, name, value })
  },
}

const getters = {
  getParameters: (state) => (page) => {
    return page.parameters || {}
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
