/**
 * User Permissions Service
 * Handles API communication for user permission management
 */
export default (client) => {
  return {
    /**
     * Get all user permission rules for a table
     */
    fetchAll(tableId) {
      return client.get(`/database/tables/${tableId}/user-permissions/`)
    },

    /**
     * Create a new user permission rule
     */
    create(tableId, values) {
      return client.post(`/database/tables/${tableId}/user-permissions/`, values)
    },

    /**
     * Get user permission rule details
     */
    get(tableId, userId) {
      return client.get(`/database/tables/${tableId}/user-permissions/${userId}/`)
    },

    /**
     * Update user permission rule
     */
    update(tableId, userId, values) {
      return client.patch(`/database/tables/${tableId}/user-permissions/${userId}/`, values)
    },

    /**
     * Revoke user permissions (soft delete)
     */
    delete(tableId, userId) {
      return client.delete(`/database/tables/${tableId}/user-permissions/${userId}/`)
    },

    /**
     * Get comprehensive user permissions summary
     */
    getSummary(tableId, userId) {
      return client.get(`/database/tables/${tableId}/user-permissions/${userId}/summary/`)
    },

    /**
     * Get user's filtered view for the table
     */
    getFilteredView(tableId) {
      return client.get(`/database/tables/${tableId}/user-permissions/filtered-view/`)
    },

    /**
     * Refresh user's filtered view
     */
    refreshFilteredView(tableId) {
      return client.post(`/database/tables/${tableId}/user-permissions/filtered-view/`)
    },

    /**
     * Get audit logs for user permissions changes
     */
    getAuditLogs(tableId, params = {}) {
      return client.get(`/database/tables/${tableId}/user-permissions/audit-logs/`, { params })
    },

    /**
     * Check if current user can manage permissions for a table
     */
    canManagePermissions(tableId) {
      return client.get(`/database/tables/${tableId}/user-permissions/can-manage/`)
    },

    /**
     * Get available users that can have permissions assigned
     */
    getAvailableUsers(tableId) {
      return client.get(`/database/tables/${tableId}/user-permissions/available-users/`)
    }
  }
}