import { client } from './client'

export default {
  fetchAll(groupId = null) {
    const groupUrl = groupId !== null ? `group/${groupId}/` : ''
    return client.get(`/applications/${groupUrl}`)
  },
  create(groupId, values) {
    return client.post(`/applications/group/${groupId}/`, values)
  },
  get(applicationId) {
    return client.get(`/applications/${applicationId}/`)
  },
  update(applicationId, values) {
    return client.patch(`/applications/${applicationId}/`, values)
  },
  delete(applicationId) {
    return client.delete(`/applications/${applicationId}/`)
  },
}
