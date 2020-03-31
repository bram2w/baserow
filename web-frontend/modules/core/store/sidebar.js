export const state = () => ({
  collapsed: false,
})

export const mutations = {
  SET_COLLAPSED(state, collapsed) {
    state.collapsed = collapsed
  },
}

export const actions = {
  toggleCollapsed({ commit, getters }, value) {
    if (value === undefined) {
      value = !getters.isCollapsed
    }
    commit('SET_COLLAPSED', value)
  },
}

export const getters = {
  isCollapsed(state) {
    return !!state.collapsed
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
