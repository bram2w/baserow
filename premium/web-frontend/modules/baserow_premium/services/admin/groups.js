import baseService from '@baserow_premium/crud_table/baseService'

export default (client) => {
  return Object.assign(baseService(client, '/admin/groups/'), {
    delete(groupId) {
      return client.delete(`/admin/groups/${groupId}/`)
    },
  })
}
