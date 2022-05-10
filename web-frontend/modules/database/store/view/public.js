import { getToken, setToken } from '@baserow/modules/core/utils/auth'

export const state = () => ({
  authToken: null,
})

export const mutations = {
  SET_AUTH_TOKEN(state, value) {
    state.authToken = value
  },
}

export const actions = {
  setAuthTokenFromCookies({ commit }, { slug }) {
    const token = getToken(this.app, slug)
    commit('SET_AUTH_TOKEN', token)
    return token
  },
  setAuthToken({ commit }, { slug, token }) {
    setToken(token, this.app, slug)
    commit('SET_AUTH_TOKEN', token)
  },
}

export const getters = {
  getAuthToken(state) {
    return state.authToken
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
