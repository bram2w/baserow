export default (client) => {
  return {
    assignRole(subjectId, subjectType, groupId, scopeId, scopeType, roleUid) {
      client.post(`/role/${groupId}/`, {
        subject_id: subjectId,
        subject_type: subjectType,
        scope_id: scopeId,
        scope_type: scopeType,
        role: roleUid,
      })
    },
  }
}
