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
  user: null,
  additional: {},
  webSocketId: null,
  // Indicates whether a token should be set persistently as a cookie using the
  // `setToken` function.
  preventSetToken: false,
  untrustedClientSessionId: uuidv4(),
})

export const mutations = {
  /* eslint-disable camelcase */
  SET_USER_DATA(state, { access_token, refresh_token, user, ...additional }) {
    state.token = access_token
    state.refreshToken = refresh_token
    state.token_data = jwtDecode(state.token)
    /* eslint-enable camelcase */
    state.user = user
    // Additional entries in the response payload could have been added via the
    // backend user data registry. We want to store them in the `additional` state so
    // that it can be used by other modules.
    state.additional = additional
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
  CLEAR_USER_DATA(state) {
    state.token = null
    state.user = null
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
}

export const actions = {
  /**
   * Authenticate a user by his email and password. If successful commit the
   * token to the state and start the refresh timeout to stay authenticated.
   */
  async login({ commit, dispatch, getters }, { email, password }) {
    const { data } = await AuthService(this.$client).login(email, password)
    commit('SET_USER_DATA', data)

    if (!getters.getPreventSetToken) {
      setToken(getters.refreshToken, this.app)
    }
    dispatch('startRefreshTimeout')
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
    setToken(data.refresh_token, this.app)
    commit('SET_USER_DATA', data)
    dispatch('startRefreshTimeout')
  },
  /**
   * Logs off the user by removing the token as a cookie and clearing the user
   * data.
   */
  async logoff({ commit, dispatch }) {
    unsetToken(this.app)
    unsetGroupCookie(this.app)
    commit('CLEAR_USER_DATA')
    await dispatch('group/clearAll', {}, { root: true })
    await dispatch('group/unselect', {}, { root: true })
    await dispatch('job/clearAll', {}, { root: true })
  },
  /**
   * Refresh the existing token. If successful commit the new token and start a
   * new refresh timeout. If unsuccessful the existing cookie and user data is
   * cleared.
   */
  async refresh({ commit, dispatch, getters }, refreshToken) {
    try {
      const { data } = await AuthService(this.$client).refresh(refreshToken)
      // if ROTATE_REFRESH_TOKEN=False in the backend the response will not contain
      // a new refresh token. In that case we keep using the old originally one stored in the cookie.
      commit('SET_USER_DATA', { refresh_token: refreshToken, ...data })

      if (!getters.getPreventSetToken) {
        setToken(getters.refreshToken, this.app)
      }
      dispatch('startRefreshTimeout')
    } catch (error) {
      // If the server can't be reached because of a network error we want to
      // fail hard so that the correct error message is shown.
      if (error.response === undefined) {
        throw error
      }

      // The token could not be refreshed, this means the token is no longer
      // valid and the user not logged in anymore.
      unsetToken(this.app)
      commit('CLEAR_USER_DATA')

      // @TODO we might want to do something here, trigger some event, show
      //       show the user a login popup or redirect to the login page.
    }
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

    // The token expires within a given time. When 80% of that time has expired we want
    // to fetch a new token.
    this.refreshTimeout = setTimeout(() => {
      dispatch('refresh', getters.refreshToken)
      commit('SET_REFRESHING', false)
    }, Math.floor((getters.tokenExpireSeconds / 100) * 80) * 1000)
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
    commit('UPDATE_USER_DATA', { user: data })
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
  },
  forceSetUserData({ commit }, data) {
    commit('SET_USER_DATA', data)
  },
  preventSetToken({ commit }) {
    commit('SET_PREVENT_SET_TOKEN', true)
  },
}

export const getters = {
  isAuthenticated(state) {
    return !!state.user
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
  /**
   * Returns the amount of seconds it will take before the tokes expires.
   * @TODO figure out what happens if the browser and server time are not in
   *       sync.
   */
  tokenExpireSeconds(state) {
    const now = Math.ceil(new Date().getTime() / 1000)
    return state.token_data.exp - now
  },
  getAdditionalUserData(state) {
    return state.additional
  },
  getPreventSetToken(state) {
    return state.preventSetToken
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
