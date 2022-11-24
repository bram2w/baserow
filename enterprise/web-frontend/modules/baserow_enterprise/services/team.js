import baseService from '@baserow/modules/core/crudTable/baseService'

export default (client) => {
  return Object.assign(
    baseService(client, ({ groupId }) => `/teams/group/${groupId}/`, false),
    {
      fetchAll(groupId) {
        return client.get(`/teams/group/${groupId}/`)
      },
      create(groupId, values) {
        return client.post(`/teams/group/${groupId}/`, values)
      },
      update(id, values) {
        return client.put(`/teams/${id}/`, values)
      },
      delete(id) {
        return client.delete(`/teams/${id}/`)
      },
      createSubject(teamId, baseUrl, values) {
        values.base_url = baseUrl
        return client.post(`/teams/${teamId}/subjects/`, values)
      },
      fetchAllSubjects(teamId) {
        return client.get(`/teams/${teamId}/subjects/`)
      },
      deleteSubject(teamId, subjectId) {
        return client.delete(`/teams/${teamId}/subjects/${subjectId}/`)
      },
    }
  )
}
