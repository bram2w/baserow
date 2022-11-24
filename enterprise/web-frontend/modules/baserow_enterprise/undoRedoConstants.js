// The different types of undo/redo scopes available for the enterprise module.
export const ENTERPRISE_ACTION_SCOPES = {
  teams_in_group(groupId) {
    return {
      teams_in_group: groupId,
    }
  },
}
