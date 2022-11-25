export default (client) => {
  return {
    assignRole(subjectId, subjectType, groupId, scopeId, scopeType, roleUid) {
      return client.post(`/role/${groupId}/`, {
        subject_id: subjectId,
        subject_type: subjectType,
        scope_id: scopeId,
        scope_type: scopeType,
        role: roleUid,
      })
    },
    assignRoleBatch(groupId, items) {
      return client.post(`/role/${groupId}/batch/`, {
        items,
      })
    },
    getRoleAssignments(groupId, scopeId, scopeType) {
      return client.get(`/role/${groupId}/`, {
        params: {
          scope_id: scopeId,
          scope_type: scopeType,
        },
      })
    },
  }
}
