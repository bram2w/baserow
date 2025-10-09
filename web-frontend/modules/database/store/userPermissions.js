/**
 * User Permissions Store
 * Manages state for user permission rules and filtered views
 */
import UserPermissionsService from '@baserow/modules/database/services/userPermissions'

export const state = () => ({
  // All user permission rules for the current table
  rules: [],
  // Current user's filtered view settings
  filteredView: null,
  // Loading states
  loading: false,
  loadingRules: false,
  loadingFilteredView: false,
  // Audit logs
  auditLogs: [],
  loadingAuditLogs: false,
  // Available users for permission assignment
  availableUsers: [],
  // Current user's permission capabilities
  canManage: false,
})

export const mutations = {
  SET_RULES(state, rules) {
    state.rules = rules
  },
  ADD_RULE(state, rule) {
    const existingIndex = state.rules.findIndex(r => r.user.id === rule.user.id)
    if (existingIndex >= 0) {
      state.rules.splice(existingIndex, 1, rule)
    } else {
      state.rules.push(rule)
    }
  },
  UPDATE_RULE(state, { userId, values }) {
    const rule = state.rules.find(r => r.user.id === userId)
    if (rule) {
      Object.assign(rule, values)
    }
  },
  REMOVE_RULE(state, userId) {
    const index = state.rules.findIndex(r => r.user.id === userId)
    if (index >= 0) {
      state.rules.splice(index, 1)
    }
  },
  SET_FILTERED_VIEW(state, filteredView) {
    state.filteredView = filteredView
  },
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_LOADING_RULES(state, loading) {
    state.loadingRules = loading
  },
  SET_LOADING_FILTERED_VIEW(state, loading) {
    state.loadingFilteredView = loading
  },
  SET_AUDIT_LOGS(state, logs) {
    state.auditLogs = logs
  },
  SET_LOADING_AUDIT_LOGS(state, loading) {
    state.loadingAuditLogs = loading
  },
  SET_AVAILABLE_USERS(state, users) {
    state.availableUsers = users
  },
  SET_CAN_MANAGE(state, canManage) {
    state.canManage = canManage
  },
  CLEAR_STATE(state) {
    state.rules = []
    state.filteredView = null
    state.auditLogs = []
    state.availableUsers = []
    state.canManage = false
    state.loading = false
    state.loadingRules = false
    state.loadingFilteredView = false
    state.loadingAuditLogs = false
  }
}

export const actions = {
  /**
   * Fetch all user permission rules for a table
   */
  async fetchRules({ commit }, tableId) {
    commit('SET_LOADING_RULES', true)
    try {
      const { data } = await UserPermissionsService(this.$client).fetchAll(tableId)
      commit('SET_RULES', data)
      return data
    } catch (error) {
      commit('SET_RULES', [])
      throw error
    } finally {
      commit('SET_LOADING_RULES', false)
    }
  },

  /**
   * Create a new user permission rule
   */
  async createRule({ commit, dispatch }, { tableId, values }) {
    commit('SET_LOADING', true)
    try {
      const { data } = await UserPermissionsService(this.$client).create(tableId, values)
      commit('ADD_RULE', data)
      
      // Refresh filtered view if this affects current user
      if (data.user.id === this.$auth.user?.id) {
        await dispatch('fetchFilteredView', tableId)
      }
      
      return data
    } catch (error) {
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  /**
   * Update an existing user permission rule
   */
  async updateRule({ commit, dispatch }, { tableId, userId, values }) {
    commit('SET_LOADING', true)
    try {
      const { data } = await UserPermissionsService(this.$client).update(tableId, userId, values)
      commit('UPDATE_RULE', { userId, values: data })
      
      // Refresh filtered view if this affects current user
      if (userId === this.$auth.user?.id) {
        await dispatch('fetchFilteredView', tableId)
      }
      
      return data
    } catch (error) {
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  /**
   * Revoke user permissions
   */
  async revokeRule({ commit, dispatch }, { tableId, userId }) {
    commit('SET_LOADING', true)
    try {
      await UserPermissionsService(this.$client).delete(tableId, userId)
      commit('REMOVE_RULE', userId)
      
      // Clear filtered view if this affects current user
      if (userId === this.$auth.user?.id) {
        commit('SET_FILTERED_VIEW', null)
      }
    } catch (error) {
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  /**
   * Fetch user's filtered view for a table
   */
  async fetchFilteredView({ commit }, tableId) {
    commit('SET_LOADING_FILTERED_VIEW', true)
    try {
      const { data } = await UserPermissionsService(this.$client).getFilteredView(tableId)
      commit('SET_FILTERED_VIEW', data)
      return data
    } catch (error) {
      // If user has no permissions, this is expected
      if (error.response?.status !== 404) {
        throw error
      }
      commit('SET_FILTERED_VIEW', null)
      return null
    } finally {
      commit('SET_LOADING_FILTERED_VIEW', false)
    }
  },

  /**
   * Refresh user's filtered view
   */
  async refreshFilteredView({ commit }, tableId) {
    commit('SET_LOADING_FILTERED_VIEW', true)
    try {
      const { data } = await UserPermissionsService(this.$client).refreshFilteredView(tableId)
      commit('SET_FILTERED_VIEW', data)
      return data
    } catch (error) {
      throw error
    } finally {
      commit('SET_LOADING_FILTERED_VIEW', false)
    }
  },

  /**
   * Fetch audit logs for user permissions
   */
  async fetchAuditLogs({ commit }, { tableId, params }) {
    commit('SET_LOADING_AUDIT_LOGS', true)
    try {
      const { data } = await UserPermissionsService(this.$client).getAuditLogs(tableId, params)
      commit('SET_AUDIT_LOGS', data)
      return data
    } catch (error) {
      commit('SET_AUDIT_LOGS', [])
      throw error
    } finally {
      commit('SET_LOADING_AUDIT_LOGS', false)
    }
  },

  /**
   * Check if current user can manage permissions
   */
  async checkManagePermissions({ commit }, tableId) {
    try {
      const { data } = await UserPermissionsService(this.$client).canManagePermissions(tableId)
      commit('SET_CAN_MANAGE', data.can_manage)
      return data.can_manage
    } catch (error) {
      commit('SET_CAN_MANAGE', false)
      return false
    }
  },

  /**
   * Fetch available users for permission assignment
   */
  async fetchAvailableUsers({ commit }, tableId) {
    try {
      const { data } = await UserPermissionsService(this.$client).getAvailableUsers(tableId)
      commit('SET_AVAILABLE_USERS', data)
      return data
    } catch (error) {
      commit('SET_AVAILABLE_USERS', [])
      throw error
    }
  },

  /**
   * Get user permission summary
   */
  async getUserPermissionSummary({ commit }, { tableId, userId }) {
    try {
      const { data } = await UserPermissionsService(this.$client).getSummary(tableId, userId)
      return data
    } catch (error) {
      throw error
    }
  },

  /**
   * Clear all state when leaving table
   */
  clearState({ commit }) {
    commit('CLEAR_STATE')
  }
}

export const getters = {
  /**
   * Get user permission rule by user ID
   */
  getRuleByUserId: (state) => (userId) => {
    return state.rules.find(rule => rule.user.id === userId)
  },

  /**
   * Get users with specific role
   */
  getUsersByRole: (state) => (role) => {
    return state.rules.filter(rule => rule.role === role)
  },

  /**
   * Check if current user has specific permissions
   */
  hasPermission: (state) => (permission) => {
    if (!state.filteredView?.rule) return false
    return state.filteredView.rule.effective_permissions[permission] === true
  },

  /**
   * Get field permissions for current user
   */
  getFieldPermissions: (state) => {
    if (!state.filteredView?.rule?.field_permissions) return {}
    
    const permissions = {}
    state.filteredView.rule.field_permissions.forEach(fp => {
      permissions[fp.field.id] = fp.permission
    })
    return permissions
  },

  /**
   * Check if field is visible to current user
   */
  isFieldVisible: (state, getters) => (fieldId) => {
    const fieldPermissions = getters.getFieldPermissions
    return fieldPermissions[fieldId] !== 'hidden'
  },

  /**
   * Get users who can be assigned permissions
   */
  getAssignableUsers: (state) => {
    const assignedUserIds = state.rules.map(rule => rule.user.id)
    return state.availableUsers.filter(user => !assignedUserIds.includes(user.id))
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}