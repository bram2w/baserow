export const state = () => ({
  impersonating: false,
})

export const mutations = {
  SET_IMPERSONATING(state, value) {
    state.impersonating = value
  },
}

export const actions = {
  setImpersonating({ commit }, value) {
    commit('SET_IMPERSONATING', value)
  },
}

export const getters = {
  getImpersonating(state) {
    return state.impersonating
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
