import baseService from '@baserow/modules/core/crudTable/baseService'

export default (client) => {
  return Object.assign(baseService(client, '/admin/groups/'), {
    delete(groupId) {
      return client.delete(`/admin/groups/${groupId}/`)
    },
  })
}
