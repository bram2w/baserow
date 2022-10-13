import PermissionsService from '@baserow/modules/core/services/permissions'

export const state = () => ({
  loaded: false,
  permissions: [],
})

export const mutations = {
  SET_PERMISSIONS(state, values) {
    state.permissions = values
  },
  UPDATE_PERMISSIONS(state, values) {
    state.permissions = Object.assign({}, state.permissions, values)
  },
  SET_LOADED(state, value) {
    state.loaded = value
  },
}

export const actions = {
  async load({ commit }, group) {
    const { data } = await PermissionsService(this.$client).get(group)
    commit('SET_PERMISSIONS', data)
    commit('SET_LOADED', true)
  },
  force_update({ commit, getters }, values) {
    commit('UPDATE_PERMISSIONS', values)
  },
}

export const getters = {
  isLoaded(state) {
    return state.loaded
  },
  get(state) {
    return state.permissions
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
