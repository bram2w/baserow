export default (client) => {
  return {
    assignRole(
      subjectId,
      subjectType,
      workspaceId,
      scopeId,
      scopeType,
      roleUid
    ) {
      return client.post(`/role/${workspaceId}/`, {
        subject_id: subjectId,
        subject_type: subjectType,
        scope_id: scopeId,
        scope_type: scopeType,
        role: roleUid,
      })
    },
    assignRoleBatch(workspaceId, items) {
      return client.post(`/role/${workspaceId}/batch/`, {
        items,
      })
    },
    getRoleAssignments(workspaceId, scopeId, scopeType) {
      return client.get(`/role/${workspaceId}/`, {
        params: {
          scope_id: scopeId,
          scope_type: scopeType,
        },
      })
    },
  }
}
