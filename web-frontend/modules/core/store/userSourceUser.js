import jwtDecode from 'jwt-decode'

import UserSourceService from '@baserow/modules/core/services/userSource'

import {
  setToken,
  unsetToken,
  userSourceCookieTokenName,
} from '@baserow/modules/core/utils/auth'

export const state = () => ({
  refreshing: false,
  token: null,
  refreshToken: null,
  tokenUpdatedAt: 0,
  tokenPayload: null,
  user: {},
  authenticated: false,
})

export const mutations = {
  SET_TOKENS(state, { access, refresh, tokenUpdatedAt }) {
    state.token = access
    state.refreshToken = refresh
    state.tokenUpdatedAt = tokenUpdatedAt || new Date().getTime()
    state.tokenPayload = jwtDecode(state.token)
  },
  SET_USER_DATA(state, data) {
    state.user = { ...data }
  },
  CLEAR_USER_DATA(state) {
    state.user = {}
  },
  LOGOFF(state) {
    state.token = null
    state.refreshToken = null
    state.tokenUpdatedAt = 0
    state.tokenPayload = null
    state.user = {}
    state.authenticated = false
  },
  SET_AUTHENTICATED(state, authenticated) {
    state.authenticated = authenticated
  },
  SET_REFRESHING(state, refreshing) {
    state.refreshing = refreshing
  },
}

export const actions = {
  async forceAuthenticate({ dispatch }, { userSource, user }) {
    const {
      data: { access_token: access, refresh_token: refresh },
    } = await UserSourceService(this.$client).forceAuthenticate(
      userSource.id,
      user.id
    )
    dispatch('login', { userSource, access, refresh, setCookie: false })
  },
  async authenticate({ dispatch }, { userSource, credentials, setCookie }) {
    const {
      data: { access_token: access, refresh_token: refresh },
    } = await UserSourceService(this.$client).authenticate(
      userSource.id,
      credentials
    )
    dispatch('login', { userSource, access, refresh, setCookie })
  },
  login(
    { commit, getters },
    { access, refresh, tokenUpdatedAt, setCookie = true }
  ) {
    commit('SET_TOKENS', { access, refresh, tokenUpdatedAt })
    const tokenPayload = jwtDecode(access)
    commit('SET_USER_DATA', {
      id: tokenPayload.user_id,
      username: tokenPayload.username,
      email: tokenPayload.email,
      user_source_id: tokenPayload.user_source_id,
    })
    commit('SET_AUTHENTICATED', true)

    if (setCookie) {
      // Set the token for next page load
      setToken(this.app, getters.refreshToken, userSourceCookieTokenName, {
        sameSite: 'Strict',
      })
    }
  },

  /**
   * Logs off the user by removing the token as a cookie and clearing the user
   * data.
   */
  async logoff({ commit, getters }, { invalidateToken = true } = {}) {
    const refreshToken = getters.refreshToken
    unsetToken(this.app, userSourceCookieTokenName)
    commit('LOGOFF')

    if (refreshToken && invalidateToken) {
      await UserSourceService(this.$client).blacklistToken(refreshToken)
    }
  },

  /**
   * Refresh the existing token. If successful commit the new token and start a
   * new refresh timeout. If unsuccessful the existing cookie and user data is
   * cleared.
   */
  async refreshAuth({ getters, dispatch }, token = null) {
    const refreshToken = token || getters.refreshToken

    if (!refreshToken) {
      throw new Error('Invalid refresh token')
    }

    const tokenUpdatedAt = new Date().getTime()
    const {
      data: { refresh_token: refresh = null, access_token: access },
    } = await UserSourceService(this.$client).refreshAuth(refreshToken)

    // if ROTATE_REFRESH_TOKEN=False in the backend the response will not contain
    // a new refresh token. In that case, we keep the one we just used.
    dispatch('login', {
      refresh: refresh || refreshToken,
      access,
      tokenUpdatedAt,
    })
  },
}

export const getters = {
  isAuthenticated(state) {
    return state.authenticated
  },
  isRefreshing(state) {
    return state.refreshing
  },
  accessToken(state) {
    return state.token
  },
  refreshToken(state) {
    return state.refreshToken
  },

  getUser(state) {
    if (state.authenticated) {
      return state.user
    }
    return { email: '', id: 0, username: '' }
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
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations,
}
