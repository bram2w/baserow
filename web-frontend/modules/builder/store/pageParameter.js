const state = {
  // The parameter values
  parameters: {},
}

const mutations = {
  SET_PARAMETER(state, { name, value }) {
    state.parameters = { ...state.parameters, [name]: value }
  },
}

const actions = {
  setParameter({ commit }, { name, value }) {
    commit('SET_PARAMETER', { name, value })
  },
}

const getters = {
  getParameters: (state) => {
    return state.parameters
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
