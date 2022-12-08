import jwtDecode from 'jwt-decode'
import Vue from 'vue'
import _ from 'lodash'

import AuthService from '@baserow/modules/core/services/auth'
import { setToken, unsetToken } from '@baserow/modules/core/utils/auth'
import { unsetGroupCookie } from '@baserow/modules/core/utils/group'
import { v4 as uuidv4 } from 'uuid'

export const state = () => ({
  refreshing: false,
  token: null,
  refreshToken: null,
  tokenUpdatedAt: 0,
  tokenPayload: null,
  user: null,
  authenticated: false,
  additional: {},
  webSocketId: null,
  // Indicates whether a token should be set persistently as a cookie using the
  // `setToken` function.
  preventSetToken: false,
  untrustedClientSessionId: uuidv4(),
  userSessionExpired: false,
})

export const mutations = {
  /* eslint-disable camelcase */
  SET_USER_DATA(
    state,
    { access_token, refresh_token, user, tokenUpdatedAt, ...additional }
  ) {
    state.token = access_token
    state.refreshToken = refresh_token
    state.tokenUpdatedAt = tokenUpdatedAt || new Date().getTime()
    state.tokenPayload = jwtDecode(state.token)
    /* eslint-enable camelcase */
    state.user = user
    // Additional entries in the response payload could have been added via the
    // backend user data registry. We want to store them in the `additional` state so
    // that it can be used by other modules.
    state.additional = additional
    state.authenticated = true
    state.userSessionExpired = false
  },
  UPDATE_USER_DATA(state, { user, ...data }) {
    if (user !== undefined) {
      Object.assign(state.user, user)
    }
    // Deep merge using lodash customized to use Vue.set to maintain reactivity. Arrays
    // and other non pure object types will be overridden, objects will be merged.
    function customizer(objValue, srcValue, key, object) {
      Vue.set(object, key, srcValue)
    }
    _.mergeWith(state.additional, data, customizer)
  },
  LOGOFF(state) {
    state.token = null
    state.refreshToken = null
    state.tokenUpdatedAt = 0
    state.tokenPayload = null
    state.authenticated = false
  },
  CLEAR_USER_DATA(state) {
    state.token = null
    state.refreshToken = null
    state.tokenUpdatedAt = 0
    state.tokenPayload = null
    state.user = null
    state.authenticated = false
  },
  SET_REFRESHING(state, refreshing) {
    state.refreshing = refreshing
  },
  SET_WEB_SOCKET_ID(state, id) {
    state.webSocketId = id
  },
  SET_PREVENT_SET_TOKEN(state, value) {
    state.preventSetToken = value
  },
  SET_USER_SESSION_EXPIRED(state, expired) {
    state.userSessionExpired = expired
  },
}

export const actions = {
  /**
   * Authenticate a user by his email and password. If successful commit the
   * token to the state and start the refresh timeout to stay authenticated.
   */
  async login({ commit, getters }, { email, password }) {
    const { data } = await AuthService(this.$client).login(email, password)
    commit('SET_USER_DATA', data)

    if (!getters.getPreventSetToken) {
      setToken(this.app, getters.refreshToken)
    }
    return data.user
  },
  /**
   * Register a new user and immediately authenticate. If successful commit the
   * token to the state and start the refresh timeout to stay authenticated.
   */
  async register(
    { commit, dispatch },
    {
      email,
      name,
      password,
      language,
      groupInvitationToken = null,
      templateId = null,
    }
  ) {
    const { data } = await AuthService(this.$client).register(
      email,
      name,
      password,
      language,
      true,
      groupInvitationToken,
      templateId
    )
    setToken(this.app, data.refresh_token)
    commit('SET_USER_DATA', data)
  },
  /**
   * Logs off the user by removing the token as a cookie and clearing the user
   * data.
   */
  logoff({ commit }) {
    unsetToken(this.app)
    unsetGroupCookie(this.app)
    commit('LOGOFF')
  },
  /**
   * Clears all the user data present in any other stores.
   */
  async clearAllStoreUserData({ commit, dispatch }) {
    await dispatch('group/clearAll', {}, { root: true })
    await dispatch('group/unselect', {}, { root: true })
    await dispatch('job/clearAll', {}, { root: true })
    commit('CLEAR_USER_DATA')
  },
  /**
   * Refresh the existing token. If successful commit the new token and start a
   * new refresh timeout. If unsuccessful the existing cookie and user data is
   * cleared.
   */
  async refresh({ commit, getters, dispatch }, token = null) {
    const refreshToken = token || getters.refreshToken
    if (!refreshToken) {
      throw new Error('Invalid refresh token')
    }

    try {
      const tokenUpdatedAt = new Date().getTime()
      const { data } = await AuthService(this.$client).refresh(refreshToken)
      // if ROTATE_REFRESH_TOKEN=False in the backend the response will not contain
      // a new refresh token. In that case, we keep the one we just used.
      commit('SET_USER_DATA', {
        refresh_token: refreshToken,
        tokenUpdatedAt,
        ...data,
      })
      if (!getters.getPreventSetToken && data.refresh_token) {
        setToken(this.app, getters.refreshToken)
      }
    } catch (error) {
      unsetToken(this.app)
      unsetGroupCookie(this.app)
      if (getters.isAuthenticated) {
        dispatch('setUserSessionExpired', true)
      }
      throw error
    }
  },
  /**
   * The web socket id is generated by the backend when connecting to the real time
   * updates web socket. This id will be added to each AJAX request so the backend
   * knows not to send any real time changes to the sender.
   */
  setWebSocketId({ commit }, webSocketId) {
    commit('SET_WEB_SOCKET_ID', webSocketId)
  },
  /**
   * Updates the account information is the authenticated user.
   */
  async update({ getters, commit, dispatch }, values) {
    const { data } = await AuthService(this.$client).update(values)
    dispatch('forceUpdateUserData', { user: data })
    dispatch(
      'group/forceUpdateGroupUserAttributes',
      {
        userId: getters.getUserId,
        values: {
          name: data.first_name,
        },
      },
      {
        root: true,
      }
    )
    return data
  },
  forceUpdateUserData({ commit }, data) {
    commit('UPDATE_USER_DATA', data)
    this.app.$bus.$emit('user-data-updated', data)
  },
  forceSetUserData({ commit }, data) {
    commit('SET_USER_DATA', data)
  },
  preventSetToken({ commit }) {
    commit('SET_PREVENT_SET_TOKEN', true)
  },
  setUserSessionExpired({ commit }, value) {
    unsetToken(this.app)
    unsetGroupCookie(this.app)
    commit('SET_USER_SESSION_EXPIRED', value)
  },
}

export const getters = {
  isAuthenticated(state) {
    return state.authenticated
  },
  isRefreshing(state) {
    return state.refreshing
  },
  token(state) {
    return state.token
  },
  refreshToken(state) {
    return state.refreshToken
  },
  webSocketId(state) {
    return state.webSocketId
  },
  getUserObject(state) {
    return state.user
  },
  getName(state) {
    return state.user ? state.user.first_name : ''
  },
  getUsername(state) {
    return state.user ? state.user.username : ''
  },
  getUserId(state) {
    return state.user ? state.user.id : null
  },
  isStaff(state) {
    return state.user ? state.user.is_staff : false
  },
  getUntrustedClientSessionId(state) {
    return state.untrustedClientSessionId
  },
  shouldRefreshToken: (state) => () => {
    // the user must be authenticated to refresh the token
    if (!state.authenticated) {
      return false
    }

    const data = state.tokenPayload
    const now = new Date().getTime()
    const tokenLifespan = (data.exp - data.iat) * 1000
    return (now - state.tokenUpdatedAt) / tokenLifespan > 0.8
  },
  getAdditionalUserData(state) {
    return state.additional
  },
  getPreventSetToken(state) {
    return state.preventSetToken
  },
  isUserSessionExpired: (state) => {
    return state.userSessionExpired
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
