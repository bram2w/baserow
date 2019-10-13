import jwtDecode from 'jwt-decode'

import AuthService from '@/services/auth'
import { setToken, unsetToken } from '@/utils/auth'
import { unsetGroupCookie } from '@/utils/group'

export const state = () => ({
  refreshing: false,
  token: null,
  user: null
})

export const mutations = {
  SET_USER_DATA(state, { token, user }) {
    state.token = token
    state.token_data = jwtDecode(token)
    state.user = user
  },
  CLEAR_USER_DATA(state) {
    state.token = null
    state.user = null
  },
  SET_REFRESHING(state, refreshing) {
    state.refreshing = refreshing
  }
}

export const actions = {
  /**
   * Authenticate a user by his email and password. If successful commit the
   * token to the state and start the refresh timeout to stay authenticated.
   */
  login({ commit, dispatch }, { email, password }) {
    return AuthService.login(email, password).then(({ data }) => {
      setToken(data.token, this.app.$cookies)
      commit('SET_USER_DATA', data)
      dispatch('startRefreshTimeout')
    })
  },
  /**
   * Register a new user and immediately authenticate. If successful commit the
   * token to the state and start the refresh timeout to stay authenticated.
   */
  register({ commit, dispatch }, { email, name, password }) {
    return AuthService.register(email, name, password, true).then(
      ({ data }) => {
        setToken(data.token, this.app.$cookies)
        commit('SET_USER_DATA', data)
        dispatch('startRefreshTimeout')
      }
    )
  },
  /**
   * Logs off the user by removing the token as a cookie and clearing the user
   * data.
   */
  logoff({ commit, dispatch }) {
    unsetToken(this.app.$cookies)
    unsetGroupCookie(this.app.$cookies)
    commit('CLEAR_USER_DATA')
    dispatch('group/clearAll', {}, { root: true })
    dispatch('group/unselect', {}, { root: true })
  },
  /**
   * Refresh the existing token. If successful commit the new token and start a
   * new refresh timeout. If unsuccessful the existing cookie and user data is
   * cleared.
   */
  refresh({ commit, state, dispatch }, token) {
    return AuthService.refresh(token)
      .then(({ data }) => {
        setToken(data.token, this.app.$cookies)
        commit('SET_USER_DATA', data)
        dispatch('startRefreshTimeout')
      })
      .catch(() => {
        // The token could not be refreshed, this means the token is no longer
        // valid and the user not logged in anymore.
        unsetToken(this.app.$cookies)
        commit('CLEAR_USER_DATA')

        // @TODO we might want to do something here, trigger some event, show
        //       show the user a login popup or redirect to the login page.
      })
  },
  /**
   * Because the token expires within a configurable time, we need to keep
   * refreshing the token before that happens. This process may only happen in
   * the browser because that is where we measure if the user still has the
   * application open.
   */
  startRefreshTimeout({ getters, commit, dispatch }) {
    if (!process.browser) return

    clearTimeout(this.refreshTimeout)
    commit('SET_REFRESHING', true)

    this.refreshTimeout = setTimeout(() => {
      dispatch('refresh', getters.token)
      commit('SET_REFRESHING', false)
    }, (getters.tokenExpireSeconds - 10) * 1000)
  }
}

export const getters = {
  isAuthenticated(state) {
    return !!state.user
  },
  isRefreshing(state) {
    return state.refresh
  },
  token(state) {
    return state.token
  },
  getName(state) {
    return state.user ? state.user.first_name : ''
  },
  getNameAbbreviation(state) {
    return state.user ? state.user.first_name.split('')[0] : ''
  },
  getEmail(state) {
    return state.user ? state.user.email : ''
  },
  /**
   * Returns the amount of seconds it will take before the tokes expires.
   * @TODO figure out what happens if the browser and server time are not in
   *       sync.
   */
  tokenExpireSeconds(state) {
    const now = Math.ceil(new Date().getTime() / 1000)
    return state.token_data.exp - now
  }
}
